from unittest.mock import Mock

from workload_profile_controller.backend import ResourceStatus
from workload_profile_controller.config import Config, ProfileConfig, ResourceConfig
from workload_profile_controller.controller import Controller


def make_config():
    return Config(
        resources={
            "monitoring": ResourceConfig(
                name="monitoring",
                description="Monitoring workload",
            ),
            "application": ResourceConfig(
                name="application",
                description="Application workload",
            ),
            "compute": ResourceConfig(
                name="compute",
                description="Compute workload",
            ),
        },
        profiles={
            "profile1": ProfileConfig(
                name="profile1",
                description="Normal operation",
                running=("monitoring", "application"),
                stopped=("compute",),
            ),
            "profile2": ProfileConfig(
                name="profile2",
                description="Compute workload",
                running=("compute",),
                stopped=("monitoring", "application"),
            ),
        },
    )


def test_get_resource_statuses():
    backend = Mock()

    backend.get_status.side_effect = [
        ResourceStatus.RUNNING,
        ResourceStatus.RUNNING,
        ResourceStatus.STOPPED,
    ]

    controller = Controller(
        config=make_config(),
        backend=backend,
    )

    statuses = controller.get_resource_statuses()

    assert statuses == {
        "monitoring": ResourceStatus.RUNNING,
        "application": ResourceStatus.RUNNING,
        "compute": ResourceStatus.STOPPED,
    }

    assert controller.state.value == "idle"
