from ...backend import Backend, ResourceStatus
from .discovery import AwsDiscovery
from .resource_client import AwsResourceClient


class AwsBackend(Backend):
    def __init__(
        self,
        discovery: AwsDiscovery,
        resource_client: AwsResourceClient,
    ):
        self._discovery = discovery
        self._resource_client = resource_client

    def get_status(self, resource_id: str) -> ResourceStatus:
        inventory = self._discovery.discover()
        resource = inventory.resolve(resource_id)

        state = self._resource_client.get_instance_state(
            resource.instance_id,
        )

        if state == "running":
            return ResourceStatus.RUNNING

        if state == "stopped":
            return ResourceStatus.STOPPED

        if state == "pending":
            return ResourceStatus.STARTING

        if state == "stopping":
            return ResourceStatus.STOPPING

        return ResourceStatus.UNKNOWN

    def start(self, resource_id: str) -> None:
        inventory = self._discovery.discover()
        resource = inventory.resolve(resource_id)

        self._resource_client.start_instance(
            resource.instance_id,
        )

    def stop(self, resource_id: str) -> None:
        inventory = self._discovery.discover()
        resource = inventory.resolve(resource_id)

        self._resource_client.stop_instance(
            resource.instance_id,
        )
