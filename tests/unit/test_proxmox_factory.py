from unittest.mock import Mock, patch

from workload_profile_controller.backends.proxmox.config import ProxmoxConfig
from workload_profile_controller.backends.proxmox.factory import create_proxmox_backend


def test_create_proxmox_backend_builds_dependencies():
    config = ProxmoxConfig(
        host="proxmox.example",
        node="node01",
        user="controller@pve",
        token_name="controller",
        token_secret="secret",
    )

    with patch(
        "workload_profile_controller.backends.proxmox.factory.load_proxmox_config",
        return_value=config,
    ) as load_config:
        with patch(
            "workload_profile_controller.backends.proxmox.factory.ProxmoxToken"
        ) as token_class:
            with patch(
                "workload_profile_controller.backends.proxmox.factory.ProxmoxHttpClient"
            ) as http_client_class:
                with patch(
                    "workload_profile_controller.backends.proxmox.factory.ProxmoxResourceClient"
                ) as resource_client_class:
                    with patch(
                        "workload_profile_controller.backends.proxmox.factory.ProxmoxDiscovery"
                    ) as discovery_class:
                        with patch(
                            "workload_profile_controller.backends.proxmox.factory.TaskWaiter"
                        ) as task_waiter_class:
                            with patch(
                                "workload_profile_controller.backends.proxmox.factory.ProxmoxBackend"
                            ) as backend_class:
                                token = Mock()
                                http_client = Mock()
                                resource_client = Mock()
                                discovery = Mock()
                                task_waiter = Mock()
                                backend = Mock()

                                token_class.return_value = token
                                http_client_class.return_value = http_client
                                resource_client_class.return_value = resource_client
                                discovery_class.return_value = discovery
                                task_waiter_class.return_value = task_waiter
                                backend_class.return_value = backend

                                result = create_proxmox_backend()

    assert result is backend

    load_config.assert_called_once_with()

    token_class.assert_called_once_with(
        user="controller@pve",
        token_name="controller",
        secret="secret",
    )

    http_client_class.assert_called_once_with(
        config=config,
        token=token,
    )

    resource_client_class.assert_called_once_with(
        http_client=http_client,
        node="node01",
        shutdown_timeout=config.shutdown_timeout,
    )

    discovery_class.assert_called_once_with(
        resource_client=resource_client,
    )

    task_waiter_class.assert_called_once_with(
        get_status=resource_client.get_task_status,
        timeout=config.task_timeout,
    )

    backend_class.assert_called_once_with(
        discovery=discovery,
        resource_client=resource_client,
        task_waiter=task_waiter,
    )
