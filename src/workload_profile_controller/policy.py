from dataclasses import dataclass
from enum import Enum

from .config import Config, ProfileConfig


class ActionType(Enum):
    STOP = "stop"
    START = "start"


@dataclass(frozen=True)
class TransitionAction:
    action: ActionType
    resource_id: str


@dataclass(frozen=True)
class TransitionPlan:
    actions: tuple[TransitionAction, ...]


class Policy:
    def __init__(self, config: Config):
        self._config = config

    def get_profile(self, name: str) -> ProfileConfig:
        if name not in self._config.profiles:
            raise ValueError(f"Unknown profile: {name}")

        return self._config.profiles[name]

    def list_profiles(self) -> tuple[str, ...]:
        return tuple(self._config.profiles.keys())

    def has_profile(self, name: str) -> bool:
        return name in self._config.profiles

    def build_transition_plan(
        self,
        source_profile: str,
        target_profile: str,
    ) -> TransitionPlan:
        source = self.get_profile(source_profile)
        target = self.get_profile(target_profile)

        source_running = set(source.running)
        target_running = set(target.running)

        stop = tuple(
            resource_id
            for resource_id in source.running
            if resource_id not in target_running
        )

        start = tuple(
            resource_id
            for resource_id in target.running
            if resource_id not in source_running
        )

        return TransitionPlan(
            actions=(
                *(TransitionAction(ActionType.STOP, resource_id) for resource_id in stop),
                *(TransitionAction(ActionType.START, resource_id) for resource_id in start),
            )
        )