from .auth import ProxmoxToken
from .backend import ProxmoxBackend
from .config_loader import load_proxmox_config
from .discovery import ProxmoxDiscovery
from .http_client import ProxmoxHttpClient
from .resource_client import ProxmoxResourceClient
from .task_waiter import TaskWaiter


def create_proxmox_backend() -> ProxmoxBackend:
    config = load_proxmox_config()

    token = ProxmoxToken(
        user=config.user,
        token_name=config.token_name,
        secret=config.token_secret,
    )

    http_client = ProxmoxHttpClient(
        config=config,
        token=token,
    )

    resource_client = ProxmoxResourceClient(
        http_client=http_client,
        node=config.node,
        shutdown_timeout=config.shutdown_timeout,
    )

    discovery = ProxmoxDiscovery(
        resource_client=resource_client,
    )

    task_waiter = TaskWaiter(
        get_status=resource_client.get_task_status,
        timeout=config.task_timeout,
    )

    return ProxmoxBackend(
        discovery=discovery,
        resource_client=resource_client,
        task_waiter=task_waiter,
    )
