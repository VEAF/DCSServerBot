from datetime import datetime
from pathlib import Path
from typing import Any

from lupa import LuaRuntime  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, field_validator


class ConfigError(Exception):
    pass


class Position(BaseModel):
    latitude: float
    longitude: float
    altitude: int | None = None  # not used anymore


class Zone(BaseModel):
    upgrades_used: int = Field(alias="upgradesUsed")
    side: int
    active: bool
    destroyed: dict[int, str] | list[str] | dict[Any, Any]
    extra_upgrade: dict[Any, Any] = Field(alias="extraUpgrade")
    remaining_units: dict[int, dict[int, str]] | dict[Any, Any] = Field(
        alias="remainingUnits"
    )
    first_capture_by_red: bool = Field(alias="firstCaptureByRed")
    level: int
    wasBlue: bool
    triggers: dict[str, int]
    position: Position = Field(alias="lat_long")
    hidden: bool = False
    flavor_text: str | None = Field(alias="flavorText", default=None)

    @property
    def side_color(self) -> str:
        if not self.active:
            return "darkgray"
        if self.side == 1:
            return "red"
        elif self.side == 2:
            return "blue"
        return "lightgray"

    @property
    def side_str(self) -> str:
        if not self.active:
            return "disabled"
        if self.side == 1:
            return "red"
        elif self.side == 2:
            return "blue"
        return "neutral"

    @property
    def total_units(self) -> int:
        return sum(len(group_units) for group_units in self.remaining_units.values())


class Mission(BaseModel):
    is_escort_mission: bool = Field(alias="isEscortMission")
    description: str
    title: str
    is_running: bool = Field(alias="isRunning")


class Connection(BaseModel):
    from_zone: str = Field(alias="from")
    to_zone: str = Field(alias="to")


class Player(BaseModel):
    coalition: str
    unit_type: str = Field(alias="unitType")
    player_name: str = Field(alias="playerName")
    latitude: float
    longitude: float
    altitude: float | None = None

    @property
    def side_color(self) -> str:
        if self.coalition == "red":
            return "red"
        elif self.coalition == "blue":
            return "blue"
        return "gray"


class EjectedPilot(BaseModel):
    player_name: str = Field(alias="playerName")
    latitude: float
    longitude: float
    altitude: float = 0
    lost_credits: float = Field(alias="lostCredits", default=0)


class PlayerStats(BaseModel):
    air: int = Field(alias="Air", default=0)
    SAM: int = Field(alias="SAM", default=0)
    points: float = Field(alias="Points", default=0)
    deaths: int = Field(alias="Deaths", default=0)
    zone_capture: int = Field(alias="Zone capture", default=0)
    zone_upgrade: int = Field(alias="Zone upgrade", default=0)
    CAS_mission: int = Field(alias="CAS mission", default=0)
    points_spent: int = Field(alias="Points spent", default=0)
    infantry: int = Field(alias="Infantry", default=0)
    ground_units: int = Field(alias="Ground Units", default=0)
    helo: int = Field(alias="Helo", default=0)


class Sitac(BaseModel):
    server_name: str
    updated_at: datetime
    zones: dict[str, Zone]
    player_stats: dict[str, PlayerStats] = Field(alias="playerStats")
    missions: list[Mission] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    players: list[Player] = Field(default_factory=list)
    ejected_pilots: list[EjectedPilot] = Field(
        alias="ejectedPilots", default_factory=list
    )

    @field_validator(
        "missions", "connections", "players", "ejected_pilots", mode="before"
    )
    @classmethod
    def convert_lua_table_to_list(cls, v: Any) -> list[Any]:
        """Convert Lua table (dict with numeric keys) to list."""
        if v is None:
            return []
        if isinstance(v, dict):
            return list(v.values())
        return v if isinstance(v, list) else list(v)

    @property
    def campaign_progress(self) -> float:
        """Return the campaign progress percentage (0-100).

        Progress is calculated as:
        (visible_zones - red_zones) / visible_zones * 100

        Hidden zones (hidden=True) and inactive zones (active=False) are
        excluded.
        """
        visible_zones = [z for z in self.zones.values() if not z.hidden and z.active]
        if not visible_zones:
            return 0.0
        red_zones = len([z for z in visible_zones if z.side == 1])
        return (len(visible_zones) - red_zones) / len(visible_zones) * 100


def lua_to_dict(lua_table: Any) -> dict[Any, Any] | None:
    if lua_table is None:
        return None
    result: dict[Any, Any] = {}
    for k, v in lua_table.items():
        if hasattr(v, "items"):
            v = lua_to_dict(v)
        result[k] = v
    return result


def load_sitac_from_file(file: Path, server_name: str) -> Sitac:
    """Load Sitac data from a Lua save file.

    Args:
        file: Path to the Lua save file
        server_name: Name of the DCS server instance

    Returns:
        Sitac object with parsed data
    """
    lua = LuaRuntime(unpack_returned_tuples=True)

    with open(file.absolute(), "r", encoding="utf-8") as f:
        lua_code = f.read()

    lua.execute(lua_code)

    zone_persistance = lua.globals().zonePersistance  # type: ignore[attr-defined]
    zone_persistance_dict = lua_to_dict(zone_persistance)

    # Merge zonesDetails into zones (new format support)
    # In new format, flavorText is stored in zonesDetails instead of directly in zones
    zones_details = zone_persistance_dict.get("zonesDetails", {})  # type: ignore[union-attr]
    if zones_details and "zones" in zone_persistance_dict:  # type: ignore[operator]
        for zone_name, details in zones_details.items():
            if zone_name in zone_persistance_dict["zones"]:  # type: ignore[index]
                zone_persistance_dict["zones"][zone_name].update(details)  # type: ignore[index]

    return Sitac(
        server_name=server_name,
        **zone_persistance_dict,  # type: ignore[arg-type]
        updated_at=datetime.fromtimestamp(file.stat().st_mtime),
    )


def get_foothold_status_path(instance_home: Path) -> Path:
    """Get path to foothold.status file for a server instance.

    Args:
        instance_home: DCS instance home directory (e.g., Saved Games/DCS.release_server)

    Returns:
        Path to foothold.status file
    """
    return instance_home / "Missions" / "Saves" / "foothold.status"


def is_foothold_server(instance_home: Path) -> bool:
    """Check if a server instance is running Foothold.

    Args:
        instance_home: DCS instance home directory

    Returns:
        True if foothold.status exists
    """
    return get_foothold_status_path(instance_home).is_file()


def detect_foothold_mission_path(instance_home: Path) -> Path | None:
    """Detect the current Foothold mission save file path.

    Args:
        instance_home: DCS instance home directory

    Returns:
        Path to mission save file, or None if not found
    """
    file_status = get_foothold_status_path(instance_home)

    if not file_status.is_file():
        return None

    try:
        with open(file_status, "r", encoding="utf-8") as f:
            mission_file_path = Path(f.readline().strip())
            if mission_file_path.is_file():
                return mission_file_path
    except (OSError, ValueError):
        pass

    return None


def get_sitac_range(sitac: Sitac) -> tuple[Position, Position]:
    """Get the geographic bounding box of all zones.

    Args:
        sitac: Sitac object

    Returns:
        Tuple of (min_position, max_position)
    """
    if not sitac.zones:
        raise ValueError("sitac without zones")
    first_zone = sitac.zones[next(iter(sitac.zones))]

    min_lat, max_lat = first_zone.position.latitude, first_zone.position.latitude
    min_long, max_long = first_zone.position.longitude, first_zone.position.longitude

    for zone in sitac.zones.values():
        min_lat, max_lat = (
            min(min_lat, zone.position.latitude),
            max(max_lat, zone.position.latitude),
        )
        min_long, max_long = (
            min(min_long, zone.position.longitude),
            max(max_long, zone.position.longitude),
        )

    return Position(latitude=min_lat, longitude=min_long), Position(
        latitude=max_lat, longitude=max_long
    )


def get_sitac_center(sitac: Sitac) -> Position:
    """Get the geographic center of all zones.

    Args:
        sitac: Sitac object

    Returns:
        Center position
    """
    min_pos, max_pos = get_sitac_range(sitac)

    return Position(
        latitude=(max_pos.latitude + min_pos.latitude) / 2,
        longitude=(max_pos.longitude + min_pos.longitude) / 2,
    )
