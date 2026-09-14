from collections.abc import Mapping, Sequence

from .inventory import AwsInventory, AwsResource
from .resource_client import AwsResourceClient


class AwsDiscovery:
    def __init__(self, resource_client: AwsResourceClient):
        self._resource_client = resource_client

    def discover(self) -> AwsInventory:
        return self.build_inventory(
            reservations=self._resource_client.list_instances(),
        )

    @staticmethod
    def build_inventory(
        reservations: Sequence[Mapping[str, object]],
    ) -> AwsInventory:
        resources = []

        for reservation in reservations:
            instances = reservation.get("Instances", [])

            if not isinstance(instances, Sequence):
                continue

            for instance in instances:
                if not isinstance(instance, Mapping):
                    continue

                resource = AwsDiscovery._build_resource(instance)

                if resource is not None:
                    resources.append(resource)

        return AwsInventory(resources)

    @staticmethod
    def _build_resource(
        data: Mapping[str, object],
    ) -> AwsResource | None:
        instance_id = data.get("InstanceId")
        tags = data.get("Tags", [])

        if not isinstance(instance_id, str):
            return None

        name = AwsDiscovery._get_name_tag(tags)

        if name is None:
            return None

        return AwsResource(
            instance_id=instance_id,
            name=name,
        )

    @staticmethod
    def _get_name_tag(
        tags: object,
    ) -> str | None:
        if not isinstance(tags, Sequence):
            return None

        for tag in tags:
            if not isinstance(tag, Mapping):
                continue

            if tag.get("Key") == "Name":
                value = tag.get("Value")

                if isinstance(value, str):
                    return value

                return None

        return None
