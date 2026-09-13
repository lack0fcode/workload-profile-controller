from enum import Enum
from typing import Protocol


class ResourceStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


class Backend(Protocol):
    def get_status(self, resource_id: str) -> ResourceStatus:
        ...

    def start(self, resource_id: str) -> None:
        ...

    def stop(self, resource_id: str) -> None:
        ...