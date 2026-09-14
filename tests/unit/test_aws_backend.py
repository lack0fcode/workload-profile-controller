from unittest.mock import MagicMock

import pytest

from workload_profile_controller.backend import ResourceStatus
from workload_profile_controller.errors import ResourceNotFoundError
from workload_profile_controller.backends.aws.backend import AwsBackend
from workload_profile_controller.backends.aws.inventory import (
    AwsInventory,
    AwsResource,
)


@pytest.fixture
def discovery():
    return MagicMock()


@pytest.fixture
def resource_client():
    return MagicMock()


@pytest.fixture
def backend(discovery, resource_client):
    return AwsBackend(
        discovery=discovery,
        resource_client=resource_client,
    )


def make_inventory(
    instance_id="i-123",
    name="monitoring",
):
    return AwsInventory(
        [
            AwsResource(
                instance_id=instance_id,
                name=name,
            ),
        ],
    )


def test_get_status_returns_running(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory()

    resource_client.get_instance_state.return_value = "running"

    status = backend.get_status("monitoring")

    assert status is ResourceStatus.RUNNING

    discovery.discover.assert_called_once_with()
    resource_client.get_instance_state.assert_called_once_with(
        "i-123",
    )


def test_get_status_returns_stopped(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory()

    resource_client.get_instance_state.return_value = "stopped"

    status = backend.get_status("monitoring")

    assert status is ResourceStatus.STOPPED


def test_get_status_returns_starting_for_pending(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory()

    resource_client.get_instance_state.return_value = "pending"

    status = backend.get_status("monitoring")

    assert status is ResourceStatus.STARTING


def test_get_status_returns_stopping_for_stopping(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory()

    resource_client.get_instance_state.return_value = "stopping"

    status = backend.get_status("monitoring")

    assert status is ResourceStatus.STOPPING


def test_get_status_returns_unknown_for_unrecognized_state(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory()

    resource_client.get_instance_state.return_value = "terminated"

    status = backend.get_status("monitoring")

    assert status is ResourceStatus.UNKNOWN


def test_start_resolves_resource_and_starts_instance(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory(
        instance_id="i-start",
        name="application",
    )

    backend.start("application")

    discovery.discover.assert_called_once_with()

    resource_client.start_instance.assert_called_once_with(
        "i-start",
    )


def test_stop_resolves_resource_and_stops_instance(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory(
        instance_id="i-stop",
        name="application",
    )

    backend.stop("application")

    discovery.discover.assert_called_once_with()

    resource_client.stop_instance.assert_called_once_with(
        "i-stop",
    )


def test_start_does_not_call_resource_client_when_resource_cannot_be_resolved(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = AwsInventory([])

    with pytest.raises(ResourceNotFoundError):
        backend.start("application")

    resource_client.start_instance.assert_not_called()


def test_stop_does_not_call_resource_client_when_resource_cannot_be_resolved(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = AwsInventory([])

    with pytest.raises(ResourceNotFoundError):
        backend.stop("application")

    resource_client.stop_instance.assert_not_called()


def test_get_status_resolves_resource_by_name(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = AwsInventory(
        [
            AwsResource(
                instance_id="i-monitoring",
                name="monitoring",
            ),
            AwsResource(
                instance_id="i-application",
                name="application",
            ),
        ],
    )

    resource_client.get_instance_state.return_value = "running"

    status = backend.get_status("application")

    assert status is ResourceStatus.RUNNING

    resource_client.get_instance_state.assert_called_once_with(
        "i-application",
    )


def test_start_propagates_resource_client_error(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory(
        instance_id="i-start",
        name="application",
    )

    resource_client.start_instance.side_effect = RuntimeError(
        "AWS start failed",
    )

    with pytest.raises(
        RuntimeError,
        match="AWS start failed",
    ):
        backend.start("application")


def test_stop_propagates_resource_client_error(
    backend,
    discovery,
    resource_client,
):
    discovery.discover.return_value = make_inventory(
        instance_id="i-stop",
        name="application",
    )

    resource_client.stop_instance.side_effect = RuntimeError(
        "AWS stop failed",
    )

    with pytest.raises(
        RuntimeError,
        match="AWS stop failed",
    ):
        backend.stop("application")
