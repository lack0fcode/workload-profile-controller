from collections.abc import Mapping, Sequence

from .inventory import (
    ProxmoxInventory,
    ProxmoxResource,
    ProxmoxResourceType,
)
from .resource_client import ProxmoxResourceClient


class ProxmoxDiscovery:
    def __init__(self, resource_client: ProxmoxResourceClient):
        self._resource_client = resource_client

    def discover(self) -> ProxmoxInventory:
        return self.build_inventory(
            qemu_data=self._resource_client.list_qemu(),
            lxc_data=self._resource_client.list_lxc(),
        )

    @staticmethod
    def build_inventory(
        qemu_data: Sequence[Mapping[str, object]],
        lxc_data: Sequence[Mapping[str, object]],
    ) -> ProxmoxInventory:
        resources = [
            *(
                ProxmoxDiscovery._build_resource(
                    item,
                    ProxmoxResourceType.QEMU,
                )
                for item in qemu_data
            ),
            *(
                ProxmoxDiscovery._build_resource(
                    item,
                    ProxmoxResourceType.LXC,
                )
                for item in lxc_data
            ),
        ]

        return ProxmoxInventory(resources)

    @staticmethod
    def _build_resource(
        data: Mapping[str, object],
        resource_type: ProxmoxResourceType,
    ) -> ProxmoxResource:
        return ProxmoxResource(
            resource_type=resource_type,
            proxmox_id=int(data["vmid"]),
            name=str(data["name"]),
        )