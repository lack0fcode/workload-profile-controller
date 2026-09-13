from dataclasses import dataclass
from enum import Enum

from ...errors import ResourceAmbiguousError, ResourceNotFoundError


class ProxmoxResourceType(Enum):
    QEMU = "qemu"
    LXC = "lxc"


@dataclass(frozen=True)
class ProxmoxResource:
    resource_type: ProxmoxResourceType
    proxmox_id: int
    name: str


class ProxmoxInventory:
    def __init__(self, resources: list[ProxmoxResource]):
        self._resources = tuple(
            sorted(
                resources,
                key=lambda resource: (
                    resource.name,
                    resource.resource_type.value,
                    resource.proxmox_id,
                ),
            )
        )

    def list_resources(self) -> tuple[ProxmoxResource, ...]:
        return self._resources

    def resolve(self, name: str) -> ProxmoxResource:
        matches = tuple(
            resource
            for resource in self._resources
            if resource.name == name
        )

        if not matches:
            raise ResourceNotFoundError(
                f"Proxmox resource not found: {name}"
            )

        if len(matches) > 1:
            raise ResourceAmbiguousError(
                f"Proxmox resource name is ambiguous: {name}"
            )

        return matches[0]
