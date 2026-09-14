import pytest

from workload_profile_controller.backends.aws.inventory import (
    AwsInventory,
    AwsResource,
)
from workload_profile_controller.errors import (
    ResourceAmbiguousError,
    ResourceNotFoundError,
)


def test_aws_inventory_lists_resources():
    inventory = AwsInventory(
        [
            AwsResource(
                instance_id="i-application",
                name="application",
            ),
            AwsResource(
                instance_id="i-monitoring",
                name="monitoring",
            ),
        ]
    )

    assert inventory.list_resources() == (
        AwsResource(
            instance_id="i-application",
            name="application",
        ),
        AwsResource(
            instance_id="i-monitoring",
            name="monitoring",
        ),
    )


def test_aws_inventory_resolves_resource_by_exact_name():
    inventory = AwsInventory(
        [
            AwsResource(
                instance_id="i-gaming",
                name="gaming",
            ),
        ]
    )

    resource = inventory.resolve("gaming")

    assert resource == AwsResource(
        instance_id="i-gaming",
        name="gaming",
    )


def test_aws_inventory_rejects_unknown_name():
    inventory = AwsInventory(
        [
            AwsResource(
                instance_id="i-gaming",
                name="gaming",
            ),
        ]
    )

    with pytest.raises(
        ResourceNotFoundError,
        match="AWS resource not found: unknown",
    ):
        inventory.resolve("unknown")


def test_aws_inventory_rejects_ambiguous_name():
    inventory = AwsInventory(
        [
            AwsResource(
                instance_id="i-gaming-1",
                name="gaming",
            ),
            AwsResource(
                instance_id="i-gaming-2",
                name="gaming",
            ),
        ]
    )

    with pytest.raises(
        ResourceAmbiguousError,
        match="AWS resource name is ambiguous: gaming",
    ):
        inventory.resolve("gaming")


def test_aws_inventory_uses_exact_name_matching():
    inventory = AwsInventory(
        [
            AwsResource(
                instance_id="i-gaming",
                name="gaming",
            ),
        ]
    )

    with pytest.raises(ResourceNotFoundError):
        inventory.resolve("Gaming")

    with pytest.raises(ResourceNotFoundError):
        inventory.resolve("gaming-prod")
