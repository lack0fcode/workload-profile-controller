from .backends.proxmox.factory import create_proxmox_backend
from .config_loader import load_config
from .controller import Controller


def create_controller(config_path: str) -> Controller:
    config = load_config(config_path)
    backend = create_proxmox_backend()

    return Controller(
        config=config,
        backend=backend,
    )
