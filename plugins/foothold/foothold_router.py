from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .config import FootholdConfig
from .dependencies import get_active_sitac, get_sitac_or_none
from .foothold import Sitac, get_sitac_center

if TYPE_CHECKING:
    from .commands import Foothold


class ServerInfo(BaseModel):
    name: str
    updated_at: datetime | None


def create_router(plugin: "Foothold") -> APIRouter:
    """Create web router with plugin instance closure.

    Args:
        plugin: Foothold plugin instance

    Returns:
        Configured APIRouter
    """
    router = APIRouter()

    # Inject plugin instance into dependencies module
    import sys

    deps_module = sys.modules[__name__.rsplit(".", 1)[0] + ".dependencies"]
    deps_module.get_plugin_instance = lambda: plugin

    # Get configuration
    config = plugin.get_config()
    cfg = FootholdConfig.model_validate(config) if config else FootholdConfig()

    @router.get("", response_class=HTMLResponse)
    async def foothold_servers(request: Request) -> str:
        servers_data: list[ServerInfo] = []
        for server_name in plugin.list_foothold_servers():
            sitac = get_sitac_or_none(server_name)
            servers_data.append(
                ServerInfo(
                    name=server_name,
                    updated_at=sitac.updated_at if sitac else None,
                )
            )

        template = plugin.template_env.get_template("foothold/servers.html")
        return template.render(
            {
                "request": request,
                "servers": servers_data,
                "now": datetime.now(),
            }
        )

    @router.get("/sitac/{server}", response_class=HTMLResponse)
    async def foothold_sitac(
        request: Request, sitac: Annotated[Sitac, Depends(get_active_sitac)]
    ) -> str:
        template = plugin.template_env.get_template("foothold/sitac.html")
        return template.render(
            {
                "request": request,
                "sitac": sitac,
            }
        )

    @router.get("/map/{server}", response_class=HTMLResponse)
    async def foothold_map(
        request: Request,
        server: str,
        sitac: Annotated[Sitac, Depends(get_active_sitac)],
    ) -> str:
        template = plugin.template_env.get_template("foothold/map.html")
        map_center = get_sitac_center(sitac)

        return template.render(
            {
                "request": request,
                "sitac": sitac,
                "server": server,
                "center": [map_center.latitude, map_center.longitude],
                "progress": sitac.campaign_progress,
                "config": cfg,
            }
        )

    @router.get("/map/{server}/players", response_class=HTMLResponse)
    async def foothold_players_modal(
        sitac: Annotated[Sitac, Depends(get_active_sitac)],
    ) -> str:
        template = plugin.template_env.get_template("foothold/partials/players.html")
        return template.render({"sitac": sitac})

    @router.get("/map/{server}/zones", response_class=HTMLResponse)
    async def foothold_zones_modal(
        sitac: Annotated[Sitac, Depends(get_active_sitac)],
    ) -> str:
        template = plugin.template_env.get_template("foothold/partials/zones.html")
        return template.render({"sitac": sitac, "progress": sitac.campaign_progress})

    @router.get("/map/{server}/missions", response_class=HTMLResponse)
    async def foothold_missions_modal(
        sitac: Annotated[Sitac, Depends(get_active_sitac)],
    ) -> str:
        template = plugin.template_env.get_template("foothold/partials/missions.html")
        return template.render({"missions": sitac.missions})

    @router.get("/map/{server}/ejected", response_class=HTMLResponse)
    async def foothold_ejected_modal(
        sitac: Annotated[Sitac, Depends(get_active_sitac)],
    ) -> str:
        template = plugin.template_env.get_template("foothold/partials/ejected.html")
        return template.render({"ejected_pilots": sitac.ejected_pilots})

    return router
