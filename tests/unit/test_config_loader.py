from pathlib import Path

import pytest

from workload_profile_controller.config_loader import load_config


CONFIG_PATH = (
    Path(__file__).parent.parent
    / "fixtures"
    / "config.yaml"
)


def test_load_config():
    config = load_config(CONFIG_PATH)

    assert set(config.resources) == {
        "monitoring",
        "compute",
        "application",
    }

    assert config.resources["monitoring"].name == "monitoring"
    assert config.resources["monitoring"].description == "Monitoring workload"

    assert config.resources["compute"].name == "compute"
    assert config.resources["compute"].description == "Compute workload"

    assert config.resources["application"].name == "application"
    assert config.resources["application"].description == "Application workload"

    assert config.profiles["profile1"].description == "Normal operation"
    assert config.profiles["profile1"].running == (
        "monitoring",
        "application",
    )
    assert config.profiles["profile1"].stopped == ("compute",)

    assert config.profiles["profile2"].description == "Compute workload"
    assert config.profiles["profile2"].running == ("compute",)
    assert config.profiles["profile2"].stopped == (
        "monitoring",
        "application",
    )

    assert config.profiles["profile3"].description == "Maintenance"
    assert config.profiles["profile3"].running == ("monitoring",)
    assert config.profiles["profile3"].stopped == (
        "compute",
        "application",
    )


def test_load_config_returns_validated_config():
    config = load_config(CONFIG_PATH)

    assert set(config.resources) == {
        "monitoring",
        "compute",
        "application",
    }
    assert set(config.profiles) == {
        "profile1",
        "profile2",
        "profile3",
    }


def test_load_config_rejects_invalid_config(tmp_path):
    invalid_config = """
controller:
  vmid: 100

resources:
  monitoring:
    description: "Monitoring workload"

profiles:
  profile1:
    description: "Invalid profile"
    running:
      - monitoring
    stopped:
      - monitoring
"""

    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(invalid_config, encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(config_path)

def test_load_config_defaults_to_proxmox_backend():
    config = load_config(CONFIG_PATH)

    assert config.backend == "proxmox"


def test_load_config_accepts_aws_backend(tmp_path):
    config_data = """
backend: aws

resources:
  monitoring:
    description: "Monitoring workload"

profiles:
  profile1:
    description: "Normal operation"
    running:
      - monitoring
    stopped: []
"""

    config_path = tmp_path / "aws.yaml"
    config_path.write_text(config_data, encoding="utf-8")

    config = load_config(config_path)

    assert config.backend == "aws"