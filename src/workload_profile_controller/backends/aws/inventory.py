from dataclasses import dataclass

from ...errors import ResourceAmbiguousError, ResourceNotFoundError


@dataclass(frozen=True)
class AwsResource:
    instance_id: str
    name: str


class AwsInventory:
    def __init__(self, resources: list[AwsResource]):
        self._resources = tuple(
            sorted(
                resources,
                key=lambda resource: (
                    resource.name,
                    resource.instance_id,
                ),
            )
        )

    def list_resources(self) -> tuple[AwsResource, ...]:
        return self._resources

    def resolve(self, name: str) -> AwsResource:
        matches = tuple(
            resource
            for resource in self._resources
            if resource.name == name
        )

        if not matches:
            raise ResourceNotFoundError(
                f"AWS resource not found: {name}"
            )

        if len(matches) > 1:
            raise ResourceAmbiguousError(
                f"AWS resource name is ambiguous: {name}"
            )

        return matches[0]
