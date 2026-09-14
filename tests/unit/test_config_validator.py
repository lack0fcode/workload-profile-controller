import pytest

from workload_profile_controller.config import (
    Config,
    ProfileConfig,
    ResourceConfig,
)
from workload_profile_controller.config_validator import validate_config


def make_valid_config() -> Config:

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
        "profile3": ProfileConfig(
            name="profile3",
            description="Maintenance",
            running=("monitoring",),
            stopped=("compute", "application"),
        ),
    }

    return Config(
        resources=resources,
        profiles=profiles,
    )


# ---------------------------------------------------------------------------
# R-01 — Resources
# ---------------------------------------------------------------------------


def test_at_least_one_resource_is_required():
    config = make_valid_config()

    invalid_config = Config(
        resources={},
        profiles=config.profiles,
    )

    with pytest.raises(ValueError, match="At least one resource is required"):
        validate_config(invalid_config)


def test_resource_id_must_not_be_empty():
    config = make_valid_config()

    config.resources[""] = ResourceConfig(
        name="invalid",
        description="Invalid resource",
    )

    with pytest.raises(ValueError, match="Resource ID must not be empty"):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-02 — Resource identity
# ---------------------------------------------------------------------------


def test_resource_name_must_not_be_empty():
    config = make_valid_config()

    config.resources["monitoring"] = ResourceConfig(
        name="",
        description="Monitoring workload",
    )

    with pytest.raises(ValueError):
        validate_config(config)


def test_resource_name_must_not_be_whitespace_only():
    config = make_valid_config()

    config.resources["monitoring"] = ResourceConfig(
        name="   ",
        description="Monitoring workload",
    )

    with pytest.raises(ValueError):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-03 — Profile identity
# ---------------------------------------------------------------------------


def test_profile_names_must_match_dictionary_keys():
    config = make_valid_config()

    config.profiles["profile1"] = ProfileConfig(
        name="another-name",
        description="Normal operation",
        running=("monitoring", "application"),
        stopped=("compute",),
    )

    with pytest.raises(ValueError):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-04 — Known resources
# ---------------------------------------------------------------------------


def test_profile_cannot_reference_unknown_resource():
    config = make_valid_config()

    config.profiles["profile1"] = ProfileConfig(
        name="profile1",
        description="Normal operation",
        running=("monitoring", "application", "unknown"),
        stopped=("compute",),
    )

    with pytest.raises(ValueError):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-05 — Mutual exclusivity
# ---------------------------------------------------------------------------


def test_resource_cannot_be_running_and_stopped():
    config = make_valid_config()

    config.profiles["profile1"] = ProfileConfig(
        name="profile1",
        description="Normal operation",
        running=("monitoring", "application"),
        stopped=("monitoring", "compute"),
    )

    with pytest.raises(ValueError):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-06 — No duplicates
# ---------------------------------------------------------------------------


def test_resource_cannot_be_duplicated_in_running():
    config = make_valid_config()

    config.profiles["profile1"] = ProfileConfig(
        name="profile1",
        description="Normal operation",
        running=("monitoring", "monitoring", "application"),
        stopped=("compute",),
    )

    with pytest.raises(ValueError):
        validate_config(config)


def test_resource_cannot_be_duplicated_in_stopped():
    config = make_valid_config()

    config.profiles["profile1"] = ProfileConfig(
        name="profile1",
        description="Normal operation",
        running=("monitoring", "application"),
        stopped=("compute", "compute"),
    )

    with pytest.raises(ValueError):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-07 — Exactly one state per resource
# ---------------------------------------------------------------------------


def test_every_resource_must_appear_in_exactly_one_state():
    config = make_valid_config()

    config.profiles["profile1"] = ProfileConfig(
        name="profile1",
        description="Normal operation",
        running=("monitoring",),
        stopped=("compute",),
    )

    with pytest.raises(ValueError):
        validate_config(config)


def test_resource_cannot_be_missing_from_profile():
    config = make_valid_config()

    config.profiles["profile1"] = ProfileConfig(
        name="profile1",
        description="Normal operation",
        running=("monitoring",),
        stopped=("compute",),
    )

    with pytest.raises(ValueError):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-08 — Same resource universe across profiles
# ---------------------------------------------------------------------------


def test_all_profiles_must_manage_the_same_resource_universe():
    config = make_valid_config()

    config.profiles["profile3"] = ProfileConfig(
        name="profile3",
        description="Maintenance",
        running=("monitoring",),
        stopped=("compute",),
    )

    with pytest.raises(ValueError):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-09 — Complete deterministic state
# ---------------------------------------------------------------------------


def test_profile_must_define_a_complete_state():
    config = make_valid_config()

    config.profiles["profile2"] = ProfileConfig(
        name="profile2",
        description="Compute workload",
        running=("compute",),
        stopped=(),
    )

    with pytest.raises(ValueError):
        validate_config(config)


# ---------------------------------------------------------------------------
# R-10 — No empty profile
# ---------------------------------------------------------------------------


def test_profile_cannot_be_empty():
    config = make_valid_config()

    config.profiles["profile4"] = ProfileConfig(
        name="profile4",
        description="Empty profile",
        running=(),
        stopped=(),
    )

    with pytest.raises(ValueError):
        validate_config(config)

# ---------------------------------------------------------------------------
# R-11 — Backend
# ---------------------------------------------------------------------------


def test_proxmox_backend_is_valid():
    config = make_valid_config()

    validate_config(config)


def test_aws_backend_is_valid():
    config = make_valid_config()

    config = Config(
        resources=config.resources,
        profiles=config.profiles,
        backend="aws",
    )

    validate_config(config)


def test_unsupported_backend_is_rejected():
    config = make_valid_config()

    config = Config(
        resources=config.resources,
        profiles=config.profiles,
        backend="invalid",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported backend: invalid",
    ):
        validate_config(config)

# ---------------------------------------------------------------------------
# Valid configuration
# ---------------------------------------------------------------------------


def test_valid_config():
    config = make_valid_config()

    validate_config(config)