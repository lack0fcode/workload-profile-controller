from dataclasses import FrozenInstanceError

import pytest

from workload_profile_controller.config import (
    Config,
    ProfileConfig,
    ResourceConfig,
)


def make_config():
    resources = {
        "monitoring": ResourceConfig(
            name="monitoring",
            description="Monitoring workload",
        ),
        "compute": ResourceConfig(
            name="compute",
            description="Compute workload",
        ),
        "application": ResourceConfig(
            name="application",
            description="Application workload",
        ),
    }

    profiles = {
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
    }

    return Config(
        resources=resources,
        profiles=profiles,
    )


def test_resource_config():
    resource = ResourceConfig(
        name="monitoring",
        description="Monitoring workload",
    )

    assert resource.name == "monitoring"
    assert resource.description == "Monitoring workload"


def test_profile_config():
    profile = ProfileConfig(
        name="profile1",
        description="Normal operation",
        running=("monitoring", "application"),
        stopped=("compute",),
    )

    assert profile.name == "profile1"
    assert profile.description == "Normal operation"
    assert profile.running == ("monitoring", "application")
    assert profile.stopped == ("compute",)


def test_config_contains_all_components():
    config = make_config()

    assert config.resources["monitoring"].name == "monitoring"
    assert config.resources["compute"].name == "compute"
    assert config.resources["application"].name == "application"

    assert config.profiles["profile1"].running == (
        "monitoring",
        "application",
    )

    assert config.profiles["profile1"].stopped == (
        "compute",
    )

    assert config.profiles["profile2"].running == (
        "compute",
    )

    assert config.profiles["profile2"].stopped == (
        "monitoring",
        "application",
    )


def test_resource_config_is_immutable():
    resource = ResourceConfig(
        name="monitoring",
        description="Monitoring workload",
    )

    with pytest.raises(FrozenInstanceError):
        resource.name = "changed"


def test_profile_config_is_immutable():
    profile = ProfileConfig(
        name="profile1",
        description="Normal operation",
        running=("monitoring",),
        stopped=("compute",),
    )

    with pytest.raises(FrozenInstanceError):
        profile.description = "changed"


def test_config_is_immutable():
    config = make_config()

    with pytest.raises(FrozenInstanceError):
        config.resources = {}

def test_config_defaults_to_proxmox_backend():
    config = make_config()

    assert config.backend == "proxmox"


def test_config_accepts_aws_backend():
    config = Config(
        resources={},
        profiles={},
        backend="aws",
    )

    assert config.backend == "aws"


def test_config_backend_is_immutable():
    config = make_config()

    with pytest.raises(FrozenInstanceError):
        config.backend = "aws"