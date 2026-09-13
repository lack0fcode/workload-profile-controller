class ProxmoxHttpError(Exception):
    def __init__(
        self,
        status_code: int,
        reason: str,
    ):
        self.status_code = status_code
        self.reason = reason

        super().__init__(
            f"Proxmox API request failed: "
            f"HTTP {status_code} {reason}"
        )
