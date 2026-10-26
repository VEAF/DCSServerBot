"""Optional, read-only diagnostics of the Windows machine that runs the bot, over SSH.

Only what the RestAPI cannot tell: the DCS processes as Windows sees them (a DCS left running that the
bot no longer knows about blocks a restart), free disk space, crash reports, and which process holds a
port. Each diagnostic is a FIXED PowerShell script below; the only parameters are integers checked
here. There is no way to run any other command, and nothing here can stop, start or kill a process.

The scripts go through ``powershell -EncodedCommand``, so they reach PowerShell unchanged whatever the
remote default shell is (cmd.exe or PowerShell). ``ssh`` is the system's OpenSSH client in batch mode:
it authenticates with the user's own keys and ``~/.ssh/config`` and never asks for a password.
"""
from __future__ import annotations

import asyncio
import base64
import json

from .config import SshConfig

__all__ = ["SshError", "SCRIPTS", "build_command", "run"]


class SshError(Exception):
    pass


_DCS_PROCESSES = r"""
$p = Get-CimInstance Win32_Process -Filter "Name='DCS_server.exe' OR Name='DCS.exe'"
@($p | ForEach-Object {
  [pscustomobject]@{
    pid = $_.ProcessId; name = $_.Name; started = $_.CreationDate.ToString('o')
    memory_mb = [math]::Round($_.WorkingSetSize / 1MB); command_line = $_.CommandLine
  }
}) | ConvertTo-Json -Depth 3
"""

_DISK_SPACE = r"""
@(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
  [pscustomobject]@{
    drive = $_.DeviceID; free_gb = [math]::Round($_.FreeSpace / 1GB, 1); size_gb = [math]::Round($_.Size / 1GB, 1)
  }
}) | ConvertTo-Json -Depth 3
"""

_CRASH_EVENTS = r"""
$since = (Get-Date).AddHours(-{hours})
$events = Get-WinEvent -FilterHashtable @{{LogName='Application'; ProviderName='Application Error','Application Hang','Windows Error Reporting'; StartTime=$since}} -ErrorAction SilentlyContinue
@($events | Where-Object {{ $_.Message -match 'DCS' }} | Select-Object -First 50 | ForEach-Object {{
  [pscustomobject]@{{
    time = $_.TimeCreated.ToString('o'); provider = $_.ProviderName; id = $_.Id
    message = $_.Message.Substring(0, [Math]::Min(1500, $_.Message.Length))
  }}
}}) | ConvertTo-Json -Depth 3
"""

_PORT_OWNER = r"""
$port = {port}
$rows = @()
$rows += @(Get-NetUDPEndpoint -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {{
  [pscustomobject]@{{ protocol = 'udp'; address = $_.LocalAddress; pid = $_.OwningProcess }} }})
$rows += @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {{
  [pscustomobject]@{{ protocol = 'tcp'; address = $_.LocalAddress; pid = $_.OwningProcess }} }})
@($rows | ForEach-Object {{
  $proc = Get-Process -Id $_.pid -ErrorAction SilentlyContinue
  $_ | Add-Member -NotePropertyName process -NotePropertyValue ($(if ($proc) {{ $proc.ProcessName }} else {{ $null }})) -PassThru
}}) | ConvertTo-Json -Depth 3
"""

#: the only scripts this module can run
SCRIPTS = {
    "dcs_processes": _DCS_PROCESSES,
    "disk_space": _DISK_SPACE,
    "crash_events": _CRASH_EVENTS,
    "port_owner": _PORT_OWNER,
}


def _script(name: str, **params: int) -> str:
    if name not in SCRIPTS:
        raise SshError(f"Unknown diagnostic '{name}'.")
    for key, value in params.items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise SshError(f"{key} must be an integer.")
    template = SCRIPTS[name]
    return template.format(**params) if params else template


def build_command(config: SshConfig, name: str, **params: int) -> list[str]:
    """The ``ssh`` argument list for a diagnostic (no shell is involved on this side)."""
    encoded = base64.b64encode(_script(name, **params).encode("utf-16-le")).decode("ascii")
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
    if config.port:
        command += ["-p", str(config.port)]
    if config.user:
        command += ["-l", config.user]
    command += ["--", config.host, f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}"]
    return command


async def run(config: SshConfig, name: str, timeout: float = 60, **params: int):
    """Run a diagnostic and return its JSON result (a list)."""
    command = build_command(config, name, **params)
    try:
        process = await asyncio.create_subprocess_exec(*command, stdin=asyncio.subprocess.DEVNULL,
                                                       stdout=asyncio.subprocess.PIPE,
                                                       stderr=asyncio.subprocess.PIPE)
    except FileNotFoundError:
        raise SshError("The 'ssh' client is not installed or not on the PATH.") from None
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        raise SshError(f"No answer over SSH within {timeout:g} s.") from None
    if process.returncode != 0:
        message = stderr.decode("utf-8", errors="replace").strip()[-500:]
        raise SshError(f"SSH to '{config.host}' failed (exit {process.returncode}): {message}")
    text = stdout.decode("utf-8", errors="replace").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except ValueError:
        raise SshError(f"Unexpected answer over SSH: {text[:300]}") from None
    return data if isinstance(data, list) else [data]
