from unittest.mock import Mock

import pytest

from workload_profile_controller.backends.proxmox.discovery import ProxmoxDiscovery
from workload_profile_controller.backends.proxmox.http_client import ProxmoxHttpClient
from workload_profile_controller.backends.proxmox.inventory import (
    ProxmoxInventory,
    ProxmoxResource,
    ProxmoxResourceType,
)
from workload_profile_controller.backends.proxmox.resource_client import (
    ProxmoxResourceClient,
)
from workload_profile_controller.backends.proxmox.task import TaskStatus
from workload_profile_controller.errors import (
    ResourceAmbiguousError,
    ResourceNotFoundError,
)


def test_proxmox_resource_type_values():
    assert ProxmoxResourceType.QEMU.value == "qemu"
    assert ProxmoxResourceType.LXC.value == "lxc"


def test_proxmox_resource_can_represent_qemu():
    resource = ProxmoxResource(
        resource_type=ProxmoxResourceType.QEMU,
        proxmox_id=169,
        name="compute",
    )

    assert resource.resource_type == ProxmoxResourceType.QEMU
    assert resource.proxmox_id == 169
    assert resource.name == "compute"


def test_proxmox_resource_can_represent_lxc():
    resource = ProxmoxResource(
        resource_type=ProxmoxResourceType.LXC,
        proxmox_id=200,
        name="database",
    )

    assert resource.resource_type == ProxmoxResourceType.LXC
    assert resource.proxmox_id == 200
    assert resource.name == "database"


def test_proxmox_resource_is_immutable():
    resource = ProxmoxResource(
        resource_type=ProxmoxResourceType.QEMU,
        proxmox_id=169,
        name="compute",
    )

    try:
        resource.name = "other"
    except AttributeError:
        pass
    else:
        raise AssertionError("ProxmoxResource should be immutable")


def test_equal_resources_are_equal():
    first = ProxmoxResource(
        resource_type=ProxmoxResourceType.QEMU,
        proxmox_id=169,
        name="compute",
    )

    second = ProxmoxResource(
        resource_type=ProxmoxResourceType.QEMU,
        proxmox_id=169,
        name="compute",
    )

    assert first == second


def test_inventory_returns_resources_in_deterministic_order():
    resources = [
        ProxmoxResource(
            ProxmoxResourceType.QEMU,
            999,
            "application",
        ),
        ProxmoxResource(
            ProxmoxResourceType.QEMU,
            169,
            "compute",
        ),
        ProxmoxResource(
            ProxmoxResourceType.QEMU,
            101,
            "monitoring",
        ),
    ]

    inventory = ProxmoxInventory(resources)

    assert inventory.list_resources() == (
       resources[0],
        resources[1],
        resources[2],
    )


def test_inventory_resolves_resource_by_exact_name():
    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = ProxmoxInventory([resource])

    assert inventory.resolve("compute") == resource


def test_inventory_does_not_resolve_different_case():
    resource = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    inventory = ProxmoxInventory([resource])

    with pytest.raises(ResourceNotFoundError):
        inventory.resolve("Compute")


def test_inventory_raises_not_found_for_unknown_name():
    inventory = ProxmoxInventory(
        [
            ProxmoxResource(
                ProxmoxResourceType.QEMU,
                169,
                "compute",
            )
        ]
    )

    with pytest.raises(
        ResourceNotFoundError,
        match="Proxmox resource not found: database",
    ):
        inventory.resolve("database")


def test_inventory_raises_ambiguous_for_duplicate_name():
    first = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    second = ProxmoxResource(
        ProxmoxResourceType.LXC,
        200,
        "compute",
    )

    inventory = ProxmoxInventory([first, second])

    with pytest.raises(
        ResourceAmbiguousError,
        match="Proxmox resource name is ambiguous: compute",
    ):
        inventory.resolve("compute")


def test_inventory_allows_same_name_only_when_there_is_one_match():
    resource = ProxmoxResource(
        ProxmoxResourceType.LXC,
        200,
        "database",
    )

    inventory = ProxmoxInventory([resource])

    assert inventory.resolve("database") is resource

def test_list_qemu_requests_qemu_resources_from_proxmox():
    http_client = Mock(spec=ProxmoxHttpClient)

    http_client.request.return_value = [
        {
            "vmid": 101,
            "name": "monitoring",
            "status": "running",
        },
        {
            "vmid": 169,
            "name": "compute",
            "status": "stopped",
        },
    ]

    client = ProxmoxResourceClient(
        http_client=http_client,
        node="pve-node-01",
    )

    result = client.list_qemu()

    assert result == [
        {
            "vmid": 101,
            "name": "monitoring",
            "status": "running",
        },
        {
            "vmid": 169,
            "name": "compute",
            "status": "stopped",
        },
    ]

    http_client.request.assert_called_once_with(
        "GET",
        "/nodes/pve-node-01/qemu",
    )


def test_list_lxc_requests_lxc_resources_from_proxmox():
    http_client = Mock(spec=ProxmoxHttpClient)

    http_client.request.return_value = [
        {
            "vmid": 200,
            "name": "database",
            "status": "running",
        },
        {
            "vmid": 201,
            "name": "nginx",
            "status": "stopped",
        },
    ]

    client = ProxmoxResourceClient(
        http_client=http_client,
        node="pve-node-01",
    )

    result = client.list_lxc()

    assert result == [
        {
            "vmid": 200,
            "name": "database",
            "status": "running",
        },
        {
            "vmid": 201,
            "name": "nginx",
            "status": "stopped",
        },
    ]

    http_client.request.assert_called_once_with(
        "GET",
        "/nodes/pve-node-01/lxc",
    )

def test_inventory_combines_qemu_and_lxc_with_deterministic_order():
    qemu = [
        ProxmoxResource(
            ProxmoxResourceType.QEMU,
            999,
            "application",
        ),
        ProxmoxResource(
            ProxmoxResourceType.QEMU,
            169,
            "compute",
        ),
    ]

    lxc = [
        ProxmoxResource(
            ProxmoxResourceType.LXC,
            200,
            "database",
        ),
        ProxmoxResource(
            ProxmoxResourceType.LXC,
            201,
            "nginx",
        ),
    ]

    inventory = ProxmoxInventory(qemu + lxc)

    assert inventory.list_resources() == (
        qemu[0],
        qemu[1],
        lxc[0],
        lxc[1],
    )


def test_inventory_resolves_qemu_and_lxc_by_exact_name():
    compute = ProxmoxResource(
        ProxmoxResourceType.QEMU,
        169,
        "compute",
    )

    database = ProxmoxResource(
        ProxmoxResourceType.LXC,
        200,
        "database",
    )

    inventory = ProxmoxInventory(
        [
            compute,
            database,
        ]
    )

    assert inventory.resolve("compute") == compute
    assert inventory.resolve("database") == database


def test_inventory_resolution_is_exact_across_qemu_and_lxc():
    resources = [
        ProxmoxResource(
            ProxmoxResourceType.QEMU,
            169,
            "compute",
        ),
        ProxmoxResource(
            ProxmoxResourceType.LXC,
            200,
            "database",
        ),
    ]

    inventory = ProxmoxInventory(resources)

    assert inventory.resolve("compute").proxmox_id == 169
    assert inventory.resolve("database").proxmox_id == 200

    with pytest.raises(ResourceNotFoundError):
        inventory.resolve("Compute")

    with pytest.raises(ResourceNotFoundError):
        inventory.resolve("Database")

def test_discover_builds_inventory_from_qemu_and_lxc():
    resource_client = Mock(spec=ProxmoxResourceClient)

    resource_client.list_qemu.return_value = [
        {
            "vmid": 169,
            "name": "compute",
        },
    ]

    resource_client.list_lxc.return_value = [
        {
            "vmid": 999,
            "name": "application",
        },
    ]

    discovery = ProxmoxDiscovery(resource_client)

    inventory = discovery.discover()

    assert inventory.list_resources() == (
        ProxmoxResource(
            ProxmoxResourceType.LXC,
            999,
            "application",
        ),
        ProxmoxResource(
            ProxmoxResourceType.QEMU,
            169,
            "compute",
        ),
    )

    resource_client.list_qemu.assert_called_once_with()
    resource_client.list_lxc.assert_called_once_with()

def test_proxmox_resource_client_get_qemu_status():
    http_client = Mock(spec=ProxmoxHttpClient)

    http_client.request.return_value = {
        "vmid": 169,
        "name": "compute",
        "status": "running",
    }

    client = ProxmoxResourceClient(
        http_client,
        "pve-node-01",
    )

    result = client.get_qemu_status(169)

    assert result == {
        "vmid": 169,
        "name": "compute",
        "status": "running",
    }

    http_client.request.assert_called_once_with(
        "GET",
        "/nodes/pve-node-01/qemu/169/status/current",
    )


def test_proxmox_resource_client_get_lxc_status():
    http_client = Mock(spec=ProxmoxHttpClient)

    http_client.request.return_value = {
        "vmid": 999,
        "name": "application",
        "status": "stopped",
    }

    client = ProxmoxResourceClient(
        http_client,
        "pve-node-01",
    )

    result = client.get_lxc_status(999)

    assert result == {
        "vmid": 999,
        "name": "application",
        "status": "stopped",
    }

    http_client.request.assert_called_once_with(
        "GET",
        "/nodes/pve-node-01/lxc/999/status/current",
    )
def test_proxmox_resource_client_start_qemu():
    http_client = Mock(spec=ProxmoxHttpClient)

    http_client.request.return_value = (
        "UPID:pve-node-01:00000001:00000001:00000001:qmstart:169"
    )

    client = ProxmoxResourceClient(
        http_client,
        "pve-node-01",
    )

    result = client.start_qemu(169)

    assert result == (
        "UPID:pve-node-01:00000001:00000001:00000001:qmstart:169"
    )

    http_client.request.assert_called_once_with(
        "POST",
        "/nodes/pve-node-01/qemu/169/status/start",
    )


def test_proxmox_resource_client_start_lxc():
    http_client = Mock(spec=ProxmoxHttpClient)

    http_client.request.return_value = (
        "UPID:pve-node-01:00000001:00000001:00000001:vzstart:999"
    )

    client = ProxmoxResourceClient(
        http_client,
        "pve-node-01",
    )

    result = client.start_lxc(999)

    assert result == (
        "UPID:pve-node-01:00000001:00000001:00000001:vzstart:999"
    )

    http_client.request.assert_called_once_with(
        "POST",
        "/nodes/pve-node-01/lxc/999/status/start",
    )
def test_proxmox_resource_client_stop_qemu():
    http_client = Mock(spec=ProxmoxHttpClient)

    http_client.request.return_value = (
        "UPID:pve-node-01:00000001:00000001:00000001:qmshutdown:169"
    )

    client = ProxmoxResourceClient(
        http_client,
        "pve-node-01",
        shutdown_timeout=120.0,
    )

    result = client.stop_qemu(169)

    assert result == (
        "UPID:pve-node-01:00000001:00000001:00000001:qmshutdown:169"
    )

    http_client.request.assert_called_once_with(
        "POST",
        "/nodes/pve-node-01/qemu/169/status/shutdown",
        data={"timeout": 120},
    )


def test_proxmox_resource_client_stop_lxc():
    http_client = Mock(spec=ProxmoxHttpClient)

    http_client.request.return_value = (
        "UPID:pve-node-01:00000001:00000001:00000001:vzshutdown:999"
    )

    client = ProxmoxResourceClient(
        http_client,
        "pve-node-01",
        shutdown_timeout=120.0,
    )

    result = client.stop_lxc(999)

    assert result == (
        "UPID:pve-node-01:00000001:00000001:00000001:vzshutdown:999"
    )

    http_client.request.assert_called_once_with(
        "POST",
        "/nodes/pve-node-01/lxc/999/status/shutdown",
        data={"timeout": 120},
    )

def test_proxmox_resource_client_get_task_status():
    http_client = Mock(spec=ProxmoxHttpClient)

    task_status = {
        "upid": (
            "UPID:pve-node-01:00000001:00000001:"
            "00000001:qmstart:169"
        ),
        "status": "stopped",
        "exitstatus": "OK",
    }

    http_client.request.return_value = task_status

    client = ProxmoxResourceClient(
        http_client,
        "pve-node-01",
    )

    upid = (
        "UPID:pve-node-01:00000001:00000001:"
        "00000001:qmstart:169"
    )

    result = client.get_task_status(upid)

    assert result == TaskStatus(
    upid=upid,
    status="stopped",
    exitstatus="OK",
)
