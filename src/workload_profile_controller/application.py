from .backends.aws.factory import create_aws_backend
from .backends.proxmox.factory import create_proxmox_backend
from .config_loader import load_config
from .controller import Controller


def create_controller(config_path: str) -> Controller:
    config = load_config(config_path)

    if config.backend == "proxmox":
        backend = create_proxmox_backend()
    elif config.backend == "aws":
        backend = create_aws_backend()
    else:
        raise ValueError(
            f"Unsupported backend: {config.backend}"
        )

    return Controller(
        config=config,
        backend=backend,
    )