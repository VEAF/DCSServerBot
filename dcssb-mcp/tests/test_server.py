"""Tests of dcssb-mcp: configuration, the RestAPI client, the tools exposed and what they send.

The bot is replaced by an httpx MockTransport that records every request, so the tests check the exact
calls each tool makes, and that nothing it should not do (a forced shutdown, a restart of every node,
a leaked key) can happen.
"""
import asyncio
import base64
import json

import httpx
import pytest

from dcssb_mcp import ssh
from dcssb_mcp.api import ApiError, RestApi
from dcssb_mcp.config import ConfigError, Secret, SshConfig, load_config
from dcssb_mcp.server import build_server, format_log

KEY = "s3cr3t-key-value"


def run(coro):
    return asyncio.run(coro)


class FakeBot:
    def __init__(self, responses=None):
        self.requests: list[httpx.Request] = []
        self.responses = responses or {}

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        status, body = self.responses.get(request.url.path, (200, {"status": "success"}))
        return httpx.Response(status, json=body)


def make(env=None, responses=None):
    env = {"DCSSB_URL": "https://bot.example.org", "DCSSB_API_KEY": KEY, **(env or {})}
    config = load_config(env=env)
    bot = FakeBot(responses)
    api = RestApi(config, transport=httpx.MockTransport(bot.handler))
    return build_server(config, api), bot, config


def tool_names(server):
    return {tool.name for tool in run(server.list_tools())}


def call(server, name, **arguments):
    result = run(server.call_tool(name, arguments))
    return result


def text_of(result) -> str:
    if isinstance(result, tuple):
        result = result[0]
    if isinstance(result, list):
        return "\n".join(getattr(part, "text", str(part)) for part in result)
    content = getattr(result, "content", None)
    if content is not None:
        return "\n".join(getattr(part, "text", str(part)) for part in content)
    return str(result)


# ============================================================================= configuration

class TestConfig:
    def test_env_only(self):
        config = load_config(env={"DCSSB_URL": "https://x.org/", "DCSSB_API_KEY": KEY, "DCSSB_PREFIX": "api"})
        assert config.base_url == "https://x.org/api"
        assert config.allow_actions is False and config.ssh is None

    def test_file_and_key_file(self, tmp_path):
        key_file = tmp_path / "key"
        key_file.write_text(KEY + "\n", encoding="utf-8")
        conf = tmp_path / "dcssb.toml"
        conf.write_text(f'url = "https://x.org"\napi_key_file = "{key_file.as_posix()}"\nallow_actions = true\n'
                        f'[ssh]\nhost = "dcs-host"\nuser = "admin"\n', encoding="utf-8")
        config = load_config(str(conf), env={})
        assert config.api_key.reveal() == KEY
        assert config.allow_actions is True
        assert config.ssh == SshConfig(host="dcs-host", user="admin")
        assert load_config(str(conf), env={"DCSSB_ALLOW_ACTIONS": "false"}).allow_actions is False

    def test_errors(self):
        with pytest.raises(ConfigError):
            load_config(env={"DCSSB_API_KEY": KEY})
        with pytest.raises(ConfigError):
            load_config(env={"DCSSB_URL": "https://x.org"})
        with pytest.raises(ConfigError):
            load_config(env={"DCSSB_URL": "ftp://x.org", "DCSSB_API_KEY": KEY})
        with pytest.raises(ConfigError):
            load_config(env={"DCSSB_URL": "https://x.org", "DCSSB_API_KEY": KEY, "DCSSB_SSH_HOST": "h; rm -rf /"})

    def test_the_key_never_prints(self):
        config = load_config(env={"DCSSB_URL": "https://x.org", "DCSSB_API_KEY": KEY})
        assert KEY not in repr(config) and KEY not in str(config.api_key) and KEY not in f"{config}"
        assert str(Secret("abc")) == "********"


# ============================================================================= tools

class TestTools:
    def test_read_only_by_default(self):
        server, _, _ = make()
        names = tool_names(server)
        assert names == {"list_servers", "list_missions", "list_log_files", "read_log"}

    def test_actions_when_allowed(self):
        server, _, _ = make({"DCSSB_ALLOW_ACTIONS": "true"})
        names = tool_names(server)
        assert {"start_server", "stop_server", "restart_server", "shutdown_server", "load_mission",
                "restart_mission", "pause_mission", "unpause_mission", "restart_node"} <= names
        assert not any("kill" in name or "command" in name or "exec" in name for name in names)
        tools = {tool.name: tool for tool in run(server.list_tools())}
        assert tools["shutdown_server"].annotations.destructive_hint is True
        assert tools["read_log"].annotations.read_only_hint is True
        assert "force" not in json.dumps(tools["shutdown_server"].input_schema)

    def test_ssh_tools_only_when_configured(self):
        server, _, _ = make({"DCSSB_SSH_HOST": "dcs-host"})
        assert {"host_dcs_processes", "host_disk_space", "host_crash_events", "host_port_owner"} <= tool_names(server)

    def test_shutdown_is_never_forced(self):
        server, bot, _ = make({"DCSSB_ALLOW_ACTIONS": "1"})
        call(server, "shutdown_server", server_name="srv")
        request = bot.requests[-1]
        assert request.method == "POST" and request.url.path == "/instance/shutdown"
        assert request.url.params["force"] == "false"
        # an argument the tool does not declare is dropped, never passed through
        call(server, "shutdown_server", server_name="srv", force=True)
        assert bot.requests[-1].url.params["force"] == "false"

    def test_node_restart_needs_a_node(self):
        server, bot, _ = make({"DCSSB_ALLOW_ACTIONS": "1"})
        before = len(bot.requests)
        with pytest.raises(Exception):
            call(server, "restart_node", node_name="")
        assert len(bot.requests) == before
        call(server, "restart_node", node_name="node1")
        assert bot.requests[-1].url.params["node_name"] == "node1"

    def test_key_header_and_password_hidden(self):
        servers = [{"name": "srv", "status": "RUNNING", "password": "letmein"}]
        server, bot, _ = make(responses={"/servers": (200, servers)})
        result = text_of(call(server, "list_servers"))
        assert "letmein" not in result
        assert bot.requests[-1].headers["X-API-Key"] == KEY

    def test_read_log_routes_and_format(self):
        answer = {"log": "dcs", "node": "node1", "server_name": "srv", "file": "dcs.log", "utc": True,
                  "lines": [{"time": "2026-10-18 10:00:00.000", "level": "ERROR", "text": "boom"}],
                  "cursor": "CUR", "rotated": True, "gap": False, "more": False, "scanned_bytes": 10}
        server, bot, _ = make(responses={"/instance/log": (200, answer)})
        result = text_of(call(server, "read_log", log="dcs", server_name="srv", level="error", tail=False))
        request = bot.requests[-1]
        assert request.url.path == "/instance/log"
        assert dict(request.url.params) == {"server_name": "srv", "level": "error", "lines": "100", "tail": "false"}
        assert "2026-10-18 10:00:00.000 ERROR boom" in result and "[cursor: CUR]" in result and "rotated" in result
        call(server, "read_log", log="dcs", server_name="srv", contains=["ASYNCNET", "401"])
        assert bot.requests[-1].url.params.get_list("contains") == ["ASYNCNET", "401"]
        call(server, "read_log", log="bot", node_name="node2")
        assert bot.requests[-1].url.path == "/node/log" and bot.requests[-1].url.params["node_name"] == "node2"

    def test_api_errors_are_sentences_without_the_key(self):
        server, _, _ = make(responses={"/instance/log": (403, {"detail": "Invalid authentication"})})
        with pytest.raises(Exception) as info:
            call(server, "read_log", log="dcs", server_name="srv")
        assert "HTTP 403" in str(info.value) and "API key" in str(info.value) and KEY not in str(info.value)

    def test_unreachable_bot(self):
        config = load_config(env={"DCSSB_URL": "https://bot.example.org", "DCSSB_API_KEY": KEY})

        def refuse(request):
            raise httpx.ConnectError("connection refused", request=request)

        api = RestApi(config, transport=httpx.MockTransport(refuse))
        with pytest.raises(ApiError) as info:
            run(api.get("/servers"))
        assert "cannot reach the bot" in str(info.value) and KEY not in str(info.value)

    def test_prompt(self):
        server, _, _ = make()
        prompt = run(server.get_prompt("diagnose_server", {"server_name": "srv"}))
        assert "ASYNCNET" in str(prompt) and "Wait for my go" in str(prompt)


def test_format_log_gap():
    text = format_log({"log": "bot", "node": "n", "file": "f", "utc": False, "lines": [], "cursor": "c",
                       "gap": True, "rotated": True, "more": True})
    assert "lines may be missing" in text and "local time" in text and "limit was reached" in text


# ============================================================================= ssh

class TestSsh:
    def decode(self, command):
        return base64.b64decode(command[-1].split()[-1]).decode("utf-16-le")

    def test_command_shape(self):
        command = ssh.build_command(SshConfig(host="dcs-host", user="admin", port=2222), "port_owner", port=10308)
        assert command[:5] == ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
        assert command[command.index("--") + 1] == "dcs-host"
        assert "$port = 10308" in self.decode(command)

    def test_only_fixed_scripts_and_integer_parameters(self):
        cfg = SshConfig(host="h")
        with pytest.raises(ssh.SshError):
            ssh.build_command(cfg, "Stop-Process")
        with pytest.raises(ssh.SshError):
            ssh.build_command(cfg, "crash_events", hours="1; Stop-Process -Name DCS")
        for name, params in (("dcs_processes", {}), ("disk_space", {}), ("crash_events", {"hours": 24}),
                             ("port_owner", {"port": 1})):
            script = self.decode(ssh.build_command(cfg, name, **params))
            assert "Stop-" not in script and "Remove-" not in script and "Kill" not in script
