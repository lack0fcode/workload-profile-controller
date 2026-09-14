from unittest.mock import MagicMock

from workload_profile_controller.backends.aws.discovery import (
    AwsDiscovery,
)
from workload_profile_controller.backends.aws.inventory import (
    AwsResource,
)


def test_build_inventory_from_ec2_reservations():
    reservations = [
        {
            "Instances": [
                {
                    "InstanceId": "i-monitoring",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "monitoring",
                        },
                    ],
                },
                {
                    "InstanceId": "i-application",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "application",
                        },
                    ],
                },
            ],
        },
        {
            "Instances": [
                {
                    "InstanceId": "i-gaming",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "gaming",
                        },
                    ],
                },
            ],
        },
    ]

    inventory = AwsDiscovery.build_inventory(reservations)

    assert inventory.list_resources() == (
        AwsResource(
            instance_id="i-application",
            name="application",
        ),
        AwsResource(
            instance_id="i-gaming",
            name="gaming",
        ),
        AwsResource(
            instance_id="i-monitoring",
            name="monitoring",
        ),
    )


def test_build_inventory_ignores_instance_without_name_tag():
    reservations = [
        {
            "Instances": [
                {
                    "InstanceId": "i-without-name",
                    "Tags": [
                        {
                            "Key": "Environment",
                            "Value": "test",
                        },
                    ],
                },
            ],
        },
    ]

    inventory = AwsDiscovery.build_inventory(reservations)

    assert inventory.list_resources() == ()


def test_build_inventory_ignores_instance_without_instance_id():
    reservations = [
        {
            "Instances": [
                {
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "gaming",
                        },
                    ],
                },
            ],
        },
    ]

    inventory = AwsDiscovery.build_inventory(reservations)

    assert inventory.list_resources() == ()


def test_build_inventory_finds_name_tag_regardless_of_tag_order():
    reservations = [
        {
            "Instances": [
                {
                    "InstanceId": "i-gaming",
                    "Tags": [
                        {
                            "Key": "Environment",
                            "Value": "test",
                        },
                        {
                            "Key": "Name",
                            "Value": "gaming",
                        },
                    ],
                },
            ],
        },
    ]

    inventory = AwsDiscovery.build_inventory(reservations)

    assert inventory.list_resources() == (
        AwsResource(
            instance_id="i-gaming",
            name="gaming",
        ),
    )


def test_build_inventory_ignores_invalid_reservation_data():
    reservations = [
        {
            "Instances": "invalid",
        },
        {
            "Instances": [
                "invalid",
            ],
        },
    ]

    inventory = AwsDiscovery.build_inventory(reservations)

    assert inventory.list_resources() == ()


def test_discover_builds_inventory_from_resource_client():
    resource_client = MagicMock()

    resource_client.list_instances.return_value = [
        {
            "Instances": [
                {
                    "InstanceId": "i-monitoring",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "monitoring",
                        },
                    ],
                },
                {
                    "InstanceId": "i-gaming",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "gaming",
                        },
                    ],
                },
            ],
        },
    ]

    discovery = AwsDiscovery(resource_client)

    inventory = discovery.discover()

    assert inventory.list_resources() == (
        AwsResource(
            instance_id="i-gaming",
            name="gaming",
        ),
        AwsResource(
            instance_id="i-monitoring",
            name="monitoring",
        ),
    )

    resource_client.list_instances.assert_called_once_with()