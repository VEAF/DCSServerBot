import os
from pathlib import Path
from string import Template
from typing import Any

from ruamel.yaml import YAML

from ..config import FootholdConfig, TileLayerConfig, WebConfig, MapConfig


class AppConfig(FootholdConfig):
    """Main application configuration class extending FootholdConfig."""

    pass


def expand_env_vars(obj: Any) -> Any:
    """Recursively expand environment variables in configuration values."""
    if isinstance(obj, dict):
        return {key: expand_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [expand_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        return Template(obj).safe_substitute(os.environ)
    else:
        return obj


def load_config_str(config_dict: dict[str, Any]) -> AppConfig:
    """Load configuration from dictionary with environment variable expansion."""
    # Apply default values
    defaults = {
        "web": {"host": "0.0.0.0", "port": 8081, "title": "Foothold Sitac"},
        "map": {
            "url_tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "min_zoom": 8,
            "max_zoom": 11,
            "alternative_tiles": [],
        },
        "enabled": True,
        "update_interval": 120,
    }

    # Merge with provided config
    merged_config = {**defaults, **config_dict}

    # Expand environment variables
    expanded_config = expand_env_vars(merged_config)

    return AppConfig(**expanded_config)


def load_config(config_path: str | Path) -> AppConfig:
    """Load configuration from YAML file."""
    yaml = YAML(typ="safe")

    with open(config_path, "r") as f:
        config_dict = yaml.load(f) or {}

    return load_config_str(config_dict)
