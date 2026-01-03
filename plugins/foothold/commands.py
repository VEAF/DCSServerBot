import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import discord
import uvicorn
from discord import app_commands
from discord.ext import tasks
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from core import Plugin, Server, Status, command, utils
from services.bot import DCSServerBot

from .config import FootholdConfig
from .foothold import (
    Sitac,
    detect_foothold_mission_path,
    is_foothold_server,
    load_sitac_from_file,
)

if TYPE_CHECKING:
    from .listener import FootholdEventListener


class Foothold(Plugin["FootholdEventListener"]):
    """Foothold plugin for DCS Server Bot.

    Monitors Foothold mission save files and provides:
    - Discord commands for campaign status
    - Web interface with interactive SITAC map
    - Real-time updates of zone control and missions
    """

    def __init__(self, bot: DCSServerBot, listener: type["FootholdEventListener"]):
        super().__init__(bot, listener)

        # In-memory cache of sitacs by server name
        self.sitacs: dict[str, Sitac] = {}

        # Web server components
        self.web_app: Optional[FastAPI] = None
        self.web_server: Optional[uvicorn.Server] = None
        self.web_thread: Optional[threading.Thread] = None

        # Jinja2 environment for templates
        plugin_dir = Path(__file__).parent
        self.template_env = Environment(
            loader=FileSystemLoader(str(plugin_dir / "templates")), autoescape=True
        )

    async def cog_load(self) -> None:
        await super().cog_load()

        # Start web server
        await self.start_web_server()

        # Start polling task
        self.polling_task.add_exception_type(OSError, IOError)
        self.polling_task.start()

        self.log.info("[OK] Foothold plugin loaded")

    async def cog_unload(self) -> None:
        # Stop polling task
        if self.polling_task.is_running():
            self.polling_task.cancel()

        # Stop web server
        await self.stop_web_server()

        await super().cog_unload()
        self.log.info("[OK] Foothold plugin unloaded")

    async def start_web_server(self) -> None:
        """Start the standalone web server in a separate thread."""
        config = self.get_config()
        if not config:
            self.log.warning("[WARN] No configuration found, web server not started")
            return

        cfg = FootholdConfig.model_validate(config)

        if not cfg.enabled:
            self.log.info("[OK] Foothold web server disabled in configuration")
            return

        # Create FastAPI app
        self.web_app = FastAPI(title=cfg.web.title, version="1.0.0")

        # Mount static files
        plugin_dir = Path(__file__).parent
        self.web_app.mount(
            "/static", StaticFiles(directory=str(plugin_dir / "static")), name="static"
        )

        # Register routes
        self.register_web_routes()

        # Create uvicorn server config
        uvicorn_config = uvicorn.Config(
            self.web_app,
            host=cfg.web.host,
            port=cfg.web.port,
            log_level="info",
            access_log=False,
        )
        self.web_server = uvicorn.Server(uvicorn_config)

        # Start server in thread
        def run_server():
            asyncio.run(self.web_server.serve())

        self.web_thread = threading.Thread(
            target=run_server, daemon=True, name="FootholdWebServer"
        )
        self.web_thread.start()

        self.log.info(
            f"[OK] Foothold web server started on http://{cfg.web.host}:{cfg.web.port}/foothold"
        )

    async def stop_web_server(self) -> None:
        """Stop the web server gracefully."""
        if self.web_server:
            self.web_server.should_exit = True
            self.log.info("[OK] Foothold web server stopped")

    def register_web_routes(self) -> None:
        """Register all web routes."""
        if not self.web_app:
            return

        from .foothold_api_router import create_router as create_api_router
        from .foothold_router import create_router as create_web_router

        # API routes
        api_router = create_api_router(self)
        self.web_app.include_router(
            api_router, prefix="/api/foothold", tags=["foothold"]
        )

        # Web routes
        web_router = create_web_router(self)
        self.web_app.include_router(
            web_router, prefix="/foothold", include_in_schema=False
        )

        # Root redirect
        @self.web_app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root(request: Request) -> RedirectResponse:
            return RedirectResponse(url="/foothold")

        @self.web_app.get("/favicon.ico", include_in_schema=False)
        async def favicon() -> RedirectResponse:
            return RedirectResponse(url="/static/favicon.ico")

    def get_sitac(self, server_name: str) -> Optional[Sitac]:
        """Get cached sitac for a server.

        Args:
            server_name: Server instance name

        Returns:
            Sitac object or None if not found
        """
        return self.sitacs.get(server_name)

    def update_sitac(self, server_name: str, sitac: Sitac) -> None:
        """Update cached sitac for a server.

        Args:
            server_name: Server instance name
            sitac: New sitac data
        """
        self.sitacs[server_name] = sitac
        self.log.debug(f"[OK] Updated sitac for {server_name}")

    def remove_sitac(self, server_name: str) -> None:
        """Remove cached sitac for a server.

        Args:
            server_name: Server instance name
        """
        if server_name in self.sitacs:
            del self.sitacs[server_name]
            self.log.debug(f"[OK] Removed sitac for {server_name}")

    def list_foothold_servers(self) -> list[str]:
        """List all servers with cached sitacs.

        Returns:
            List of server names
        """
        return sorted(self.sitacs.keys())

    @tasks.loop(seconds=120)
    async def polling_task(self) -> None:
        """Periodically scan all servers for Foothold missions."""
        # Get update interval from config
        config = self.get_config()
        if config:
            cfg = FootholdConfig.model_validate(config)
            if not cfg.enabled:
                return
            # Update loop interval
            if self.polling_task.seconds != cfg.update_interval:
                self.polling_task.change_interval(seconds=cfg.update_interval)

        servers_to_remove = []

        # Scan all DCS servers
        for server_name, server in self.bot.servers.items():
            try:
                # Check if server config enables foothold
                server_config = self.get_config(server)
                if server_config:
                    server_cfg = FootholdConfig.model_validate(server_config)
                    if not server_cfg.enabled:
                        # Remove from cache if disabled
                        if server_name in self.sitacs:
                            servers_to_remove.append(server_name)
                        continue

                instance_home = Path(server.instance.home)

                # Check if server has Foothold
                if not is_foothold_server(instance_home):
                    # Remove from cache if no longer has foothold.status
                    if server_name in self.sitacs:
                        servers_to_remove.append(server_name)
                    continue

                # Detect mission save file
                mission_path = detect_foothold_mission_path(instance_home)
                if not mission_path:
                    self.log.debug(f"[WARN] No mission path found for {server_name}")
                    if server_name in self.sitacs:
                        servers_to_remove.append(server_name)
                    continue

                # Load sitac
                sitac = load_sitac_from_file(mission_path, server_name)

                # Check if data changed
                cached = self.sitacs.get(server_name)
                if not cached or cached.updated_at != sitac.updated_at:
                    self.update_sitac(server_name, sitac)
                    self.log.info(
                        f"[OK] Loaded sitac for {server_name} (updated: {sitac.updated_at})"
                    )

            except Exception as e:
                self.log.error(
                    f"[FAIL] Error scanning {server_name}: {e}", exc_info=True
                )

        # Remove servers that no longer have Foothold
        for server_name in servers_to_remove:
            self.remove_sitac(server_name)
            self.log.info(f"[OK] Removed {server_name} (Foothold disabled or missing)")

    @polling_task.before_loop
    async def before_polling_task(self) -> None:
        await self.bot.wait_until_ready()

    @command(description="Show Foothold campaign status")
    @app_commands.guild_only()
    @utils.app_has_role("DCS")
    async def foothold(
        self,
        interaction: discord.Interaction,
        server: app_commands.Transform[
            Server,
            utils.ServerTransformer(
                status=[Status.RUNNING, Status.PAUSED, Status.STOPPED]
            ),
        ],
    ) -> None:
        await interaction.response.defer(thinking=True)

        sitac = self.get_sitac(server.name)

        if not sitac:
            await interaction.followup.send(
                f"[FAIL] No Foothold data available for {server.display_name}.\n"
                f"Make sure the server is running a Foothold mission.",
                ephemeral=True,
            )
            return

        # Create rich embed
        embed = discord.Embed(
            title=f"Foothold Status - {server.display_name}",
            color=discord.Color.blue(),
            timestamp=sitac.updated_at,
        )

        # Campaign progress
        progress = sitac.campaign_progress
        progress_bar = self.create_progress_bar(progress)
        embed.add_field(
            name="Campaign Progress",
            value=f"{progress_bar} {progress:.1f}%",
            inline=False,
        )

        # Zone statistics
        visible_zones = [z for z in sitac.zones.values() if not z.hidden and z.active]
        red_zones = sum(1 for z in visible_zones if z.side == 1)
        blue_zones = sum(1 for z in visible_zones if z.side == 2)
        neutral_zones = len(visible_zones) - red_zones - blue_zones

        embed.add_field(name="Red Zones", value=str(red_zones), inline=True)
        embed.add_field(name="Blue Zones", value=str(blue_zones), inline=True)
        embed.add_field(name="Neutral Zones", value=str(neutral_zones), inline=True)

        # Missions
        active_missions = len(sitac.missions)
        running_missions = sum(1 for m in sitac.missions if m.is_running)
        embed.add_field(
            name="Active Missions",
            value=f"{running_missions}/{active_missions}",
            inline=True,
        )

        # Players
        embed.add_field(
            name="Players Online", value=str(len(sitac.players)), inline=True
        )

        # Ejected pilots
        embed.add_field(
            name="Ejected Pilots", value=str(len(sitac.ejected_pilots)), inline=True
        )

        # Data age
        age_seconds = (datetime.now() - sitac.updated_at).total_seconds()
        age_str = (
            f"{int(age_seconds)}s ago"
            if age_seconds < 60
            else f"{int(age_seconds/60)}m ago"
        )
        embed.set_footer(text=f"Last update: {age_str}")

        await interaction.followup.send(embed=embed)

    def create_progress_bar(self, percentage: float, length: int = 10) -> str:
        """Create a text-based progress bar.

        Args:
            percentage: Progress percentage (0-100)
            length: Length of the bar in characters

        Returns:
            Progress bar string
        """
        filled = int(percentage / 100 * length)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"


async def setup(bot: DCSServerBot):
    from .listener import FootholdEventListener

    await bot.add_cog(Foothold(bot, FootholdEventListener))
