from workload_profile_controller.backends.proxmox.discovery import ProxmoxDiscovery
from workload_profile_controller.backends.proxmox.inventory import ProxmoxResourceType


def test_build_inventory_converts_qemu_resources():
    qemu_data = [
        {
            "vmid": 169,
            "name": "compute",
        },
        {
            "vmid": 101,
            "name": "monitoring",
        },
    ]

    inventory = ProxmoxDiscovery.build_inventory(
        qemu_data=qemu_data,
        lxc_data=[],
    )

    assert inventory.resolve("compute").resource_type == ProxmoxResourceType.QEMU
    assert inventory.resolve("compute").proxmox_id == 169

    assert (
        inventory.resolve("monitoring").resource_type
        == ProxmoxResourceType.QEMU
    )


def test_build_inventory_converts_lxc_resources():
    lxc_data = [
        {
            "vmid": 200,
            "name": "database",
        },
        {
            "vmid": 201,
            "name": "nginx",
        },
    ]

    inventory = ProxmoxDiscovery.build_inventory(
        qemu_data=[],
        lxc_data=lxc_data,
    )

    assert inventory.resolve("database").resource_type == ProxmoxResourceType.LXC
    assert inventory.resolve("database").proxmox_id == 200

    assert inventory.resolve("nginx").resource_type == ProxmoxResourceType.LXC


def test_build_inventory_combines_qemu_and_lxc():
    qemu_data = [
        {
            "vmid": 169,
            "name": "compute",
        }
    ]

    lxc_data = [
        {
            "vmid": 200,
            "name": "database",
        }
    ]

    inventory = ProxmoxDiscovery.build_inventory(
        qemu_data=qemu_data,
        lxc_data=lxc_data,
    )

    assert inventory.resolve("compute").proxmox_id == 169
    assert inventory.resolve("database").proxmox_id == 200


def test_build_inventory_preserves_duplicate_names_for_ambiguity_detection():
    qemu_data = [
        {
            "vmid": 169,
            "name": "compute",
        }
    ]

    lxc_data = [
        {
            "vmid": 200,
            "name": "compute",
        }
    ]

    inventory = ProxmoxDiscovery.build_inventory(
        qemu_data=qemu_data,
        lxc_data=lxc_data,
    )

    from workload_profile_controller.errors import ResourceAmbiguousError

    try:
        inventory.resolve("compute")
    except ResourceAmbiguousError:
        pass
    else:
        raise AssertionError("Expected ResourceAmbiguousError")
