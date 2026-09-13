from dataclasses import dataclass


@dataclass(frozen=True)
class ProxmoxConfig:
    host: str
    node: str
    user: str
    token_name: str
    token_secret: str
    verify_tls: bool = True
    ca_file: str | None = None
    tls_server_name: str | None = None
    timeout: float = 5.0
    task_timeout: float = 120.0
    shutdown_timeout: float = 120.0