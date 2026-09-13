from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceConfig:
    name: str
    description: str


@dataclass(frozen=True)
class ProfileConfig:
    name: str
    description: str
    running: tuple[str, ...]
    stopped: tuple[str, ...]


@dataclass(frozen=True)
class Config:
    resources: dict[str, ResourceConfig]
    profiles: dict[str, ProfileConfig]