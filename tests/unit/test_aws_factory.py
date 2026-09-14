from unittest.mock import MagicMock

from workload_profile_controller.backends.aws.backend import AwsBackend
from workload_profile_controller.backends.aws.config import AwsConfig
from workload_profile_controller.backends.aws.factory import (
    create_aws_backend,
)


def test_create_aws_backend_builds_dependencies(monkeypatch):
    config = AwsConfig(
        region="us-east-1",
        profile="localstack",
        endpoint_url="http://localhost.localstack.cloud:4566",
        timeout=5.0,
        operation_timeout=120.0,
    )

    resource_client = MagicMock()
    discovery = MagicMock()

    load_config = MagicMock(return_value=config)
    resource_client_class = MagicMock(return_value=resource_client)
    discovery_class = MagicMock(return_value=discovery)

    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.factory.load_aws_config",
        load_config,
    )
    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.factory.AwsResourceClient",
        resource_client_class,
    )
    monkeypatch.setattr(
        "workload_profile_controller.backends.aws.factory.AwsDiscovery",
        discovery_class,
    )

    backend = create_aws_backend()

    assert isinstance(backend, AwsBackend)

    load_config.assert_called_once_with()

    resource_client_class.assert_called_once_with(
        config=config,
    )

    discovery_class.assert_called_once_with(
        resource_client=resource_client,
    )

    assert backend._resource_client is resource_client
    assert backend._discovery is discovery