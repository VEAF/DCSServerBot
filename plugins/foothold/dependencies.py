from typing import TYPE_CHECKING, Optional

from fastapi import HTTPException, Path as PathParam

from .foothold import Sitac

if TYPE_CHECKING:
    from .commands import Foothold


def get_plugin_instance() -> "Foothold":
    """Get the Foothold plugin instance.

    This is set by the router when it's created.
    """
    # This will be set by create_router functions
    raise NotImplementedError("Plugin instance not set")


def get_active_sitac(server: str = PathParam(...)) -> Sitac:
    """FastAPI dependency to get active sitac for a server.

    Args:
        server: Server name from path parameter

    Returns:
        Sitac object

    Raises:
        HTTPException: If server not found or no sitac data
    """
    plugin = get_plugin_instance()
    sitac = plugin.get_sitac(server)

    if not sitac:
        raise HTTPException(
            status_code=404,
            detail=f"No Foothold data available for server '{server}'. "
            f"Make sure the server is running a Foothold mission.",
        )

    return sitac


def get_sitac_or_none(server: str) -> Optional[Sitac]:
    """Get sitac for a server, or None if not found.

    Args:
        server: Server name

    Returns:
        Sitac object or None
    """
    plugin = get_plugin_instance()
    return plugin.get_sitac(server)
