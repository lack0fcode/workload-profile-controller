from unittest.mock import Mock

import pytest

from workload_profile_controller.backend import ResourceStatus
from workload_profile_controller.backends.proxmox.backend import ProxmoxBackend
from workload_profile_controller.backends.proxmox.discovery import ProxmoxDiscovery
from workload_profile_controller.backends.proxmox.inventory import (
    ProxmoxResource,
    ProxmoxResourceType,
)
from workload_profile_controller.backends.proxmox.resource_client import (
    ProxmoxResourceClient,
)
from workload_profile_controller.backends.proxmox.task import TaskStatus
from workload_profile_controller.backends.proxmox.task_waiter import TaskWaiter
from workload_profile_controller.errors import (
    TaskFailedError,
    TaskTimeoutError,
)


def test_get_status_returns_running_for_qemu():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    resource_client.get_qemu_status.return_value = {
        "vmid": 169,
        "name": "compute",
        "status": "running",
    }

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    assert backend.get_status("compute") == ResourceStatus.RUNNING

    resource_client.get_qemu_status.assert_called_once_with(169)
    resource_client.get_lxc_status.assert_not_called()


def test_get_status_returns_stopped_for_lxc():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.LXC,
        999,
        "application",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    resource_client.get_lxc_status.return_value = {
        "vmid": 999,
        "name": "application",
        "status": "stopped",
    }

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    assert backend.get_status("application") == ResourceStatus.STOPPED

    resource_client.get_lxc_status.assert_called_once_with(999)
    resource_client.get_qemu_status.assert_not_called()


def test_get_status_maps_starting_state():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    resource_client.get_qemu_status.return_value = {
        "status": "starting",
    }

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    assert backend.get_status("compute") == ResourceStatus.STARTING


def test_get_status_maps_stopping_state():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    resource_client.get_qemu_status.return_value = {
        "status": "stopping",
    }

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    assert backend.get_status("compute") == ResourceStatus.STOPPING


def test_get_status_maps_unknown_state():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    resource_client.get_qemu_status.return_value = {
        "status": "paused",
    }

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    assert backend.get_status("compute") == ResourceStatus.UNKNOWN


def test_start_starts_qemu_resource():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    backend.start("compute")

    resource_client.start_qemu.assert_called_once_with(169)
    resource_client.start_lxc.assert_not_called()


def test_start_starts_lxc_resource():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.LXC,
        999,
        "application",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    backend.start("application")

    resource_client.start_lxc.assert_called_once_with(999)
    resource_client.start_qemu.assert_not_called()


def test_stop_stops_qemu_resource():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    backend.stop("compute")

    resource_client.stop_qemu.assert_called_once_with(169)
    resource_client.stop_lxc.assert_not_called()


def test_stop_stops_lxc_resource():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.LXC,
        999,
        "application",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    backend.stop("application")

    resource_client.stop_lxc.assert_called_once_with(999)
    resource_client.stop_qemu.assert_not_called()


def test_start_waits_for_qemu_task():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    upid = "UPID:pve-node-01:00000004"

    resource_client.start_qemu.return_value = upid

    task_waiter.wait.return_value = TaskStatus(
        upid=upid,
        status="stopped",
        exitstatus="OK",
    )

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    backend.start("compute")

    resource_client.start_qemu.assert_called_once_with(169)
    task_waiter.wait.assert_called_once_with(upid)

def test_stop_waits_for_qemu_task():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    upid = "UPID:pve-node-01:00000005"

    resource_client.stop_qemu.return_value = upid

    task_waiter.wait.return_value = TaskStatus(
        upid=upid,
        status="stopped",
        exitstatus="OK",
    )

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    backend.stop("compute")

    resource_client.stop_qemu.assert_called_once_with(169)
    task_waiter.wait.assert_called_once_with(upid)


def test_stop_waits_for_lxc_task():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.LXC,
        999,
        "application",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    upid = "UPID:pve-node-01:00000006"

    resource_client.stop_lxc.return_value = upid

    task_waiter.wait.return_value = TaskStatus(
        upid=upid,
        status="stopped",
        exitstatus="OK",
    )

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    backend.stop("application")

    resource_client.stop_lxc.assert_called_once_with(999)
    task_waiter.wait.assert_called_once_with(upid)

def test_start_propagates_task_failed_error():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    upid = "UPID:pve-node-01:00000007"

    resource_client.start_qemu.return_value = upid

    task_waiter.wait.side_effect = TaskFailedError(
        f"Task failed: {upid}"
    )

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    with pytest.raises(TaskFailedError):
        backend.start("compute")

    resource_client.start_qemu.assert_called_once_with(169)
    task_waiter.wait.assert_called_once_with(upid)


def test_start_propagates_task_timeout_error():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    upid = "UPID:pve-node-01:00000008"

    resource_client.start_qemu.return_value = upid

    task_waiter.wait.side_effect = TaskTimeoutError(
        f"Task timed out: {upid}"
    )

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    with pytest.raises(TaskTimeoutError):
        backend.start("compute")

    resource_client.start_qemu.assert_called_once_with(169)
    task_waiter.wait.assert_called_once_with(upid)

def test_stop_propagates_task_failed_error():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    upid = "UPID:pve-node-01:00000009"

    resource_client.stop_qemu.return_value = upid

    task_waiter.wait.side_effect = TaskFailedError(
        f"Task failed: {upid}"
    )

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    with pytest.raises(TaskFailedError):
        backend.stop("compute")

    resource_client.stop_qemu.assert_called_once_with(169)
    task_waiter.wait.assert_called_once_with(upid)


def test_stop_propagates_task_timeout_error():
    discovery = Mock(spec=ProxmoxDiscovery)
    resource_client = Mock(spec=ProxmoxResourceClient)
    task_waiter = Mock(spec=TaskWaiter)

    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = Mock()
    inventory.resolve.return_value = resource
    discovery.discover.return_value = inventory

    upid = "UPID:pve-node-01:00000010"

    resource_client.stop_qemu.return_value = upid

    task_waiter.wait.side_effect = TaskTimeoutError(
        f"Task timed out: {upid}"
    )

    backend = ProxmoxBackend(
        discovery,
        resource_client,
        task_waiter,
    )

    with pytest.raises(TaskTimeoutError):
        backend.stop("compute")

    resource_client.stop_qemu.assert_called_once_with(169)
    task_waiter.wait.assert_called_once_with(upid)