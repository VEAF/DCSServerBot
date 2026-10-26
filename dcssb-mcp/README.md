# dcssb-mcp

A local [MCP](https://modelcontextprotocol.io) server that lets an AI assistant (Claude Code, Claude Desktop, VS Code, Cursor and any other MCP client) diagnose and operate a DCSServerBot installation through the bot's [RestAPI](../plugins/restapi/README.md).

Ask it things like:

* « Why does the Foothold server not restart? »
* « Show me the errors of the bot since 3 am. »
* « Did the Caucasus server lose its login to ED today? »
* « Restart the mission on the training server when it is empty. » (actions must be enabled, and the client asks you before each one)

It is a separate program: it lives in the bot's repository but is not loaded by the bot, has its own dependencies, and runs on **your** machine.
It only talks to the RestAPI, plus, if you configure it, a few fixed read-only checks over SSH.

## What it can and cannot do

| Tool | What it does | Available |
|---|---|---|
| `list_servers` | servers, status, mission, players, next restart (the server password is hidden) | always |
| `list_missions` | missions of a server | always |
| `list_log_files` | files of a server's `dcs.log` or of a node's bot log | always |
| `read_log` | read a log, filtered (level, text terms, time window), with a cursor to get only the new lines | always |
| `start_server`, `stop_server`, `restart_server` | the same as `/server start`, `stop`, `restart` | `allow_actions = true` |
| `shutdown_server` | graceful shutdown of the DCS process, optionally when the server is empty | `allow_actions = true` |
| `load_mission`, `restart_mission`, `pause_mission`, `unpause_mission` | mission control | `allow_actions = true` |
| `restart_node` | restart one bot node (the DCS servers keep running) | `allow_actions = true` |
| `host_dcs_processes` | DCS processes as Windows sees them (finds a leftover DCS the bot lost track of) | SSH configured |
| `host_disk_space` | free disk space | SSH configured |
| `host_crash_events` | Windows crash and hang reports mentioning DCS | SSH configured |
| `host_port_owner` | which process holds a port | SSH configured |

There is also a prompt, `diagnose_server`, that walks the assistant through a diagnosis without changing anything.

What it deliberately does **not** do, and why:

* **No process kill, ever.** The RestAPI can force a shutdown by killing DCS; this tool never asks for it. Killing a DCS process can leave its session with ED open and break the login of the next start (we have seen a 401 on another server after such a kill). The bot knows how to stop DCS properly: let it.
* **No free command.** The SSH checks are four fixed PowerShell scripts whose only parameters are numbers. There is no way to make the tool run anything else on your server.
* **No restart of every node at once**, no mission upload, no warehouse or airbase changes, no statistics.
* **Actions are off until you turn them on**, and each one is marked destructive, so your MCP client asks you before running it.

## Install

You need Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) (the bot's installer already uses it).
From the bot's folder:

```bash
cd dcssb-mcp
uv sync
uv run dcssb-mcp --version
```

You can also copy the `dcssb-mcp` folder to the machine where your assistant runs: it does not need anything else from the bot.

## Configure the bot's RestAPI

The tool needs the RestAPI plugin, with the log endpoints (`/node/log`, `/instance/log`).

1. Enable the plugin and the WebService (see the [RestAPI README](../plugins/restapi/README.md)).
2. Set an API key in `config/plugins/restapi.yaml`; generate a long random one, for instance with `python -c "import secrets; print(secrets.token_urlsafe(32))"`:
   ```yaml
   DEFAULT:
     auth:
       api_key: "<your key>"
   ```
3. Decide how the tool reaches the API:
   * **On the bot's machine**, or through an SSH tunnel (`ssh -L 9876:127.0.0.1:9876 your-server`): use `http://127.0.0.1:9876`. The log endpoints still require the key.
   * **From elsewhere**: never expose port 9876 directly. Put a reverse proxy with HTTPS in front of it (Caddy is the simplest: `bot.example.org { reverse_proxy 127.0.0.1:9876 }`) and keep the WebService listening on `127.0.0.1`.
     Requests through the internet need a JWT by default (`security.default.remote: jwt`); for this tool, allow the API key on the endpoints it uses:
     ```yaml
     DEFAULT:
       endpoints:
         servers:            {security: {remote: api_key}}
         instance/missions:  {security: {remote: api_key}}
         instance/logs:      {security: {remote: api_key}}
         instance/log:       {security: {remote: api_key}}
         node/logs:          {security: {remote: api_key}}
         node/log:           {security: {remote: api_key}}
         # only if you enable actions:
         instance/start:     {security: {remote: api_key}}
         # ... and so on for each action endpoint you want
     ```
     An endpoint rule replaces the default for the scopes it names; write `local` and `trusted` too if you need them.

## Configure the tool

Put the key in a file only you can read, and write a config file, for instance `~/.config/dcssb-mcp/config.toml`:

```toml
url = "https://bot.example.org"     # or http://127.0.0.1:9876
api_key_file = "~/.config/dcssb-mcp/api_key"
# prefix = "/api"                   # if the RestAPI has a prefix
# allow_actions = true              # start, stop, restart, shutdown, missions, node restart
# timeout = 30

# Optional: read-only checks of the bot's Windows machine over SSH.
# Uses your own SSH keys and ~/.ssh/config (an alias works); never a password.
# The server needs the Windows OpenSSH server and an account allowed to read the event log.
# [ssh]
# host = "dcs-server"
# user = "admin"
# port = 22
```

Every setting can also come from the environment: `DCSSB_URL`, `DCSSB_API_KEY_FILE` (or `DCSSB_API_KEY`), `DCSSB_PREFIX`, `DCSSB_ALLOW_ACTIONS`, `DCSSB_TIMEOUT`, `DCSSB_SSH_HOST`, `DCSSB_SSH_USER`, `DCSSB_SSH_PORT`, and `DCSSB_CONFIG` for the file itself.
The environment wins over the file.
The key is never printed: not in errors, not in tool results.

## Connect it to your assistant

**Claude Code**:

```bash
claude mcp add dcssb -- uv run --directory /path/to/DCSServerBot/dcssb-mcp dcssb-mcp --config ~/.config/dcssb-mcp/config.toml
```

**Claude Desktop, Cursor, VS Code and other clients** take the same command in their JSON configuration:

```json
{
  "mcpServers": {
    "dcssb": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/DCSServerBot/dcssb-mcp", "dcssb-mcp",
               "--config", "/home/me/.config/dcssb-mcp/config.toml"]
    }
  }
}
```

On Windows, write the paths with forward slashes or doubled backslashes.

## Example: « why does the Foothold server not restart? »

With the `diagnose_server` prompt, or just by asking, the assistant typically:

1. calls `list_servers` and sees the server in `SHUTDOWN` while the scheduler should have started it;
2. reads the bot log: `read_log log="bot" contains=["Foothold"] since="2h"`, and finds the start attempt timing out;
3. reads the DCS log: `read_log log="dcs" server_name="Foothold" contains=["ASYNCNET"] since="2h"` and sees `Login failed: 401`;
4. with SSH configured, calls `host_dcs_processes` and finds a `DCS_server.exe -w Foothold` started three hours ago that the bot no longer tracks;
5. explains this with the log lines, and proposes the gentlest fix, waiting for your go.

Later, `read_log` with the cursor of its last answer returns only the new lines, so following a restart costs a few hundred bytes per call.

## Security

* **The API key is mandatory** for the log endpoints, even on the bot's machine. Keep it in a file, not in the MCP client's JSON (which is often synced or shared).
* **Never expose the API without HTTPS.** The key travels in a header: over plain HTTP anyone on the way can read it.
* **Logs contain personal data**: player names, UCIDs, IP addresses. What the tool reads goes to your AI assistant's provider. Use it on your own servers, and follow your community's privacy rules.
* **Actions act on live servers.** Leave `allow_actions` off unless you need it, and read what the assistant proposes before you accept.
* **SSH**: use a dedicated account with the least rights that can still read processes and the event log; the tool never needs an administrator.

## Development

```bash
cd dcssb-mcp
uv sync --extra test
uv run pytest
```
