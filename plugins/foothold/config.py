from typing import Annotated
from pydantic import BaseModel, Field


class TileLayerConfig(BaseModel):
    name: str
    url: str


class WebConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8081
    title: str = "Foothold Sitac"


class MapConfig(BaseModel):
    url_tiles: str = (
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    )
    alternative_tiles: Annotated[list[TileLayerConfig], Field(default_factory=list)]
    min_zoom: int = 8
    max_zoom: int = 11


class FootholdConfig(BaseModel):
    """Configuration model for Foothold plugin."""

    enabled: bool = True
    update_interval: int = 120
    web: Annotated[WebConfig, Field(default_factory=WebConfig)]
    map: Annotated[MapConfig, Field(default_factory=MapConfig)]
