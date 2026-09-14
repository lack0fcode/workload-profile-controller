import pytest

from workload_profile_controller.backends.aws.config_loader import (
    load_aws_config,
)

def test_load_aws_config_from_environment(monkeypatch):
    monkeypatch.setenv(
        "WPC_AWS_REGION",
        "us-east-1",
    )
    monkeypatch.delenv(
        "WPC_AWS_PROFILE",
        raising=False,
    )
    monkeypatch.delenv(
        "WPC_AWS_ENDPOINT_URL",
        raising=False,
    )

    config = load_aws_config()

    assert config.region == "us-east-1"
    assert config.profile is None
    assert config.endpoint_url is None
    assert config.timeout == 5.0
    assert config.operation_timeout == 120.0


def test_load_aws_config_accepts_optional_environment_values(
    monkeypatch,
):
    monkeypatch.setenv(
        "WPC_AWS_REGION",
        "us-west-2",
    )
    monkeypatch.setenv(
        "WPC_AWS_PROFILE",
        "localstack",
    )
    monkeypatch.setenv(
        "WPC_AWS_ENDPOINT_URL",
        "http://localhost.localstack.cloud:4566",
    )
    monkeypatch.setenv(
        "WPC_AWS_TIMEOUT",
        "10.0",
    )
    monkeypatch.setenv(
        "WPC_AWS_OPERATION_TIMEOUT",
        "60.0",
    )

    config = load_aws_config()

    assert config.region == "us-west-2"
    assert config.profile == "localstack"
    assert config.endpoint_url == "http://localhost.localstack.cloud:4566"
    assert config.timeout == 10.0
    assert config.operation_timeout == 60.0


def test_load_aws_config_requires_region(monkeypatch):
    monkeypatch.delenv(
        "WPC_AWS_REGION",
        raising=False,
    )

    with pytest.raises(KeyError):
        load_aws_config()
