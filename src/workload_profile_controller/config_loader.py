from pathlib import Path

import yaml

from .config import Config, ProfileConfig, ResourceConfig
from .config_validator import validate_config


def load_config(path: str | Path) -> Config:
    config_path = Path(path)

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    resources = {
        resource_id: ResourceConfig(
            name=resource_id,
            description=resource_data.get("description", ""),
        )
        for resource_id, resource_data in data["resources"].items()
    }

    profiles = {
        name: ProfileConfig(
            name=name,
            description=profile_data.get("description", ""),
            running=tuple(profile_data.get("running", [])),
            stopped=tuple(profile_data.get("stopped", [])),
        )
        for name, profile_data in data["profiles"].items()
    }

    config = Config(
        resources=resources,
        profiles=profiles,
    )

    validate_config(config)

    return config