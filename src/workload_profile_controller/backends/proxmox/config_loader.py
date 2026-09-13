import os

from dotenv import load_dotenv

from .config import ProxmoxConfig

load_dotenv()


def load_proxmox_config() -> ProxmoxConfig:
    return ProxmoxConfig(
        host=os.environ["PVE_PROXMOX_HOST"],
        node=os.environ["PVE_PROXMOX_NODE"],
        user=os.environ["PVE_PROXMOX_USER"],
        token_name=os.environ["PVE_PROXMOX_TOKEN_NAME"],
        token_secret=os.environ["PVE_PROXMOX_TOKEN_SECRET"],
        verify_tls=os.environ.get(
            "PVE_PROXMOX_VERIFY_TLS",
            "true",
        ).lower() == "true",
        ca_file=os.environ.get(
            "PVE_PROXMOX_CA_FILE",
        ),
        tls_server_name=os.environ.get(
            "PVE_PROXMOX_TLS_SERVER_NAME",
        ),
        timeout=float(
            os.environ.get(
                "PVE_PROXMOX_TIMEOUT",
                "5.0",
            )
        
        ),
        task_timeout=float(
            os.environ.get(
                "PVE_PROXMOX_TASK_TIMEOUT",
                "120.0",
            )  
        ),
                shutdown_timeout=float(
            os.environ.get(
                "PVE_PROXMOX_SHUTDOWN_TIMEOUT",
                "120.0",
            )
        ),
    )