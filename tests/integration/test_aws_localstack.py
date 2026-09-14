from workload_profile_controller.backends.aws.config import AwsConfig
from workload_profile_controller.backends.aws.discovery import AwsDiscovery
from workload_profile_controller.backends.aws.resource_client import (
    AwsResourceClient,
)
from workload_profile_controller.application import create_controller
from workload_profile_controller.backend import ResourceStatus


def test_discover_localstack_instances():
    config = AwsConfig(
        region="us-east-1",
        profile="localstack",
        endpoint_url="http://localhost.localstack.cloud:4566",
    )

    resource_client = AwsResourceClient(config)
    discovery = AwsDiscovery(resource_client)

    inventory = discovery.discover()

    resources = inventory.list_resources()

    assert len(resources) >= 3

    names = {resource.name for resource in resources}

    assert "monitoring" in names
    assert "application" in names
    assert "gaming" in names


def test_discover_localstack_instances_resolves_resources():
    config = AwsConfig(
        region="us-east-1",
        profile="localstack",
        endpoint_url="http://localhost.localstack.cloud:4566",
    )

    resource_client = AwsResourceClient(config)
    discovery = AwsDiscovery(resource_client)

    inventory = discovery.discover()

    monitoring = inventory.resolve("monitoring")
    application = inventory.resolve("application")
    gaming = inventory.resolve("gaming")

    assert monitoring.name == "monitoring"
    assert application.name == "application"
    assert gaming.name == "gaming"

    assert monitoring.instance_id.startswith("i-")
    assert application.instance_id.startswith("i-")
    assert gaming.instance_id.startswith("i-")


def test_controller_can_transition_localstack_instances(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "WPC_AWS_REGION",
        "us-east-1",
    )
    monkeypatch.setenv(
        "WPC_AWS_PROFILE",
        "localstack",
    )
    monkeypatch.setenv(
        "WPC_AWS_ENDPOINT_URL",
        "http://localhost.localstack.cloud:4566",
    )

    config_path = tmp_path / "aws.yaml"

    config_path.write_text(
        """
backend: aws

resources:
  monitoring:
    description: "Monitoring workload"

  application:
    description: "Application workload"

  gaming:
    description: "Gaming workload"

profiles:
  all_stopped:
    description: "All workloads stopped"
    running: []
    stopped:
      - monitoring
      - application
      - gaming

  all_running:
    description: "All workloads running"
    running:
      - monitoring
      - application
      - gaming
    stopped: []
""",
        encoding="utf-8",
    )

    controller = create_controller(config_path)

    resources = (
        "monitoring",
        "application",
        "gaming",
    )

    try:
        # Normalize the LocalStack environment.
        for resource_id in resources:
            status = controller._backend.get_status(resource_id)

            if status == ResourceStatus.RUNNING:
                controller._backend.stop(resource_id)

        assert controller.reconcile() == "all_stopped"

        controller.transition(
            "all_stopped",
            "all_running",
        )

        assert controller.reconcile() == "all_running"

        statuses = controller.get_resource_statuses()

        assert statuses == {
            "monitoring": ResourceStatus.RUNNING,
            "application": ResourceStatus.RUNNING,
            "gaming": ResourceStatus.RUNNING,
        }

    finally:
        # Leave LocalStack in the stopped state.
        for resource_id in resources:
            status = controller._backend.get_status(resource_id)

            if status == ResourceStatus.RUNNING:
                controller._backend.stop(resource_id)

        assert controller.reconcile() == "all_stopped"