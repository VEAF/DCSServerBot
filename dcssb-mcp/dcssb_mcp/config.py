"""Configuration: a TOML file and/or environment variables. The API key never leaves this object.

Every setting can come from the file given with ``--config`` (or ``DCSSB_CONFIG``) or from an
environment variable; the environment wins. The API key is read from ``api_key_file`` /
``DCSSB_API_KEY_FILE`` (preferred: the key stays out of the MCP client's own configuration) or from
``api_key`` / ``DCSSB_API_KEY``. It is held in a :class:`Secret`, whose ``str`` and ``repr`` never show
it, so it cannot end up in a log line, an error message or a tool result by accident.
"""
from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["ConfigError", "Secret", "SshConfig", "Config", "load_config"]


class ConfigError(Exception):
    pass


class Secret:
    """A string that does not print itself."""

    __slots__ = ("_value",)

    def __init__(self, value: str):
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __str__(self) -> str:
        return "********"

    __repr__ = __str__

    def __bool__(self) -> bool:
        return bool(self._value)


@dataclass(frozen=True)
class SshConfig:
    """Where the optional SSH diagnostics connect. Authentication is the user's own SSH setup (keys, agent,
    ``~/.ssh/config``); no password is ever handled here."""
    host: str
    user: str | None = None
    port: int | None = None


@dataclass(frozen=True)
class Config:
    url: str
    api_key: Secret = field(repr=False)
    prefix: str = ""
    allow_actions: bool = False
    timeout: float = 30.0
    verify_tls: bool = True
    ssh: SshConfig | None = None

    @property
    def base_url(self) -> str:
        return self.url.rstrip("/") + self.prefix


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


def _bool(value, name: str) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    raise ConfigError(f"{name}: expected true or false, got '{value}'.")


def load_config(path: str | None = None, env: dict[str, str] | None = None) -> Config:
    env = os.environ if env is None else env
    path = path or env.get("DCSSB_CONFIG")
    data: dict = {}
    if path:
        try:
            data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ConfigError(f"Config file '{path}' not found.") from None
        except tomllib.TOMLDecodeError as ex:
            raise ConfigError(f"Config file '{path}' is not valid TOML: {ex}.") from None

    def get(key: str, default=None):
        return env.get(f"DCSSB_{key.upper()}", data.get(key, default))

    url = get("url")
    if not url:
        raise ConfigError("No RestAPI URL: set 'url' in the config file or DCSSB_URL.")
    url = str(url)
    if not re.match(r"^https?://", url):
        raise ConfigError(f"The RestAPI URL must start with http:// or https:// (got '{url}').")

    key = ""
    key_file = get("api_key_file")
    if key_file:
        try:
            key = Path(os.path.expanduser(str(key_file))).read_text(encoding="utf-8").strip()
        except OSError as ex:
            raise ConfigError(f"Cannot read the API key file '{key_file}' ({ex.strerror}).") from None
    else:
        key = str(get("api_key", "") or "")
    if not key:
        raise ConfigError("No API key: set 'api_key_file' (preferred) or 'api_key' in the config file, "
                          "or DCSSB_API_KEY_FILE / DCSSB_API_KEY.")

    prefix = str(get("prefix", "") or "").strip().rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = "/" + prefix

    try:
        timeout = float(get("timeout", 30))
    except ValueError:
        raise ConfigError("timeout: expected a number of seconds.") from None

    ssh = None
    ssh_data = data.get("ssh", {}) if isinstance(data.get("ssh", {}), dict) else {}
    ssh_host = env.get("DCSSB_SSH_HOST", ssh_data.get("host"))
    if ssh_host:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", str(ssh_host)):
            raise ConfigError("ssh.host: a host name or an alias of your SSH config, nothing else.")
        ssh_user = env.get("DCSSB_SSH_USER", ssh_data.get("user"))
        if ssh_user and not re.fullmatch(r"[A-Za-z0-9._\\-]+", str(ssh_user)):
            raise ConfigError("ssh.user: a user name, nothing else.")
        ssh_port = env.get("DCSSB_SSH_PORT", ssh_data.get("port"))
        try:
            port = int(ssh_port) if ssh_port else None
        except ValueError:
            raise ConfigError("ssh.port: expected a number.") from None
        ssh = SshConfig(host=str(ssh_host), user=str(ssh_user) if ssh_user else None, port=port)

    return Config(url=url, api_key=Secret(key), prefix=prefix,
                  allow_actions=_bool(get("allow_actions", False), "allow_actions"),
                  timeout=timeout, verify_tls=_bool(get("verify_tls", True), "verify_tls"), ssh=ssh)
