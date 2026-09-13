from ...backend import Backend, ResourceStatus
from .discovery import ProxmoxDiscovery
from .inventory import ProxmoxResourceType
from .resource_client import ProxmoxResourceClient
from .task_waiter import TaskWaiter


class ProxmoxBackend(Backend):
    def __init__(
        self,
        discovery: ProxmoxDiscovery,
        resource_client: ProxmoxResourceClient,
        task_waiter: TaskWaiter,
    ):
        self._discovery = discovery
        self._resource_client = resource_client
        self._task_waiter = task_waiter

    def get_status(self, resource_id: str) -> ResourceStatus:
        inventory = self._discovery.discover()
        resource = inventory.resolve(resource_id)

        if resource.resource_type == ProxmoxResourceType.QEMU:
            data = self._resource_client.get_qemu_status(
                resource.proxmox_id
            )
        elif resource.resource_type == ProxmoxResourceType.LXC:
            data = self._resource_client.get_lxc_status(
                resource.proxmox_id
            )
        else:
            raise RuntimeError(
                f"Unsupported Proxmox resource type: "
                f"{resource.resource_type}"
            )

        status = data["status"]

        if status == "running":
            return ResourceStatus.RUNNING

        if status == "stopped":
            return ResourceStatus.STOPPED

        if status == "starting":
            return ResourceStatus.STARTING

        if status == "stopping":
            return ResourceStatus.STOPPING

        return ResourceStatus.UNKNOWN

    def start(self, resource_id: str) -> None:
        inventory = self._discovery.discover()
        resource = inventory.resolve(resource_id)

        if resource.resource_type == ProxmoxResourceType.QEMU:
            upid = self._resource_client.start_qemu(
                resource.proxmox_id
            )
            self._task_waiter.wait(upid)
            return

        if resource.resource_type == ProxmoxResourceType.LXC:
            upid = self._resource_client.start_lxc(
                resource.proxmox_id
            )
            self._task_waiter.wait(upid)
            return

        raise RuntimeError(
            f"Unsupported Proxmox resource type: "
            f"{resource.resource_type}"
        )

    def stop(self, resource_id: str) -> None:
        inventory = self._discovery.discover()
        resource = inventory.resolve(resource_id)

        if resource.resource_type == ProxmoxResourceType.QEMU:
            upid = self._resource_client.stop_qemu(
                resource.proxmox_id
            )
            self._task_waiter.wait(upid)
            return

        if resource.resource_type == ProxmoxResourceType.LXC:
            upid = self._resource_client.stop_lxc(
                resource.proxmox_id
            )
            self._task_waiter.wait(upid)
            return

        raise RuntimeError(
            f"Unsupported Proxmox resource type: "
            f"{resource.resource_type}"
        )