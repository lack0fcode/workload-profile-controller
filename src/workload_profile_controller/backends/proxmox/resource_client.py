import urllib.parse

from .http_client import ProxmoxHttpClient
from .task import TaskStatus


class ProxmoxResourceClient:
    def __init__(
        self,
        http_client: ProxmoxHttpClient,
        node: str,
        shutdown_timeout: float = 120.0,
    ):
        self._http_client = http_client
        self._node = node
        self._shutdown_timeout = shutdown_timeout

    def list_qemu(self):
        return self._http_client.request(
            "GET",
            f"/nodes/{self._node}/qemu",
        )

    def list_lxc(self):
        return self._http_client.request(
            "GET",
            f"/nodes/{self._node}/lxc",
        )

    def get_qemu_status(self, proxmox_id: int):
        return self._http_client.request(
            "GET",
            f"/nodes/{self._node}/qemu/{proxmox_id}/status/current",
        )

    def get_lxc_status(self, proxmox_id: int):
        return self._http_client.request(
            "GET",
            f"/nodes/{self._node}/lxc/{proxmox_id}/status/current",
        )

    def start_qemu(self, proxmox_id: int):
        return self._http_client.request(
            "POST",
            f"/nodes/{self._node}/qemu/{proxmox_id}/status/start",
        )

    def start_lxc(self, proxmox_id: int):
        return self._http_client.request(
            "POST",
            f"/nodes/{self._node}/lxc/{proxmox_id}/status/start",
        )

    def stop_qemu(self, proxmox_id: int):
        return self._http_client.request(
            "POST",
            f"/nodes/{self._node}/qemu/{proxmox_id}/status/shutdown",
            data={
                "timeout": int(self._shutdown_timeout),
            },
        )

    def stop_lxc(self, proxmox_id: int):
        return self._http_client.request(
            "POST",
            f"/nodes/{self._node}/lxc/{proxmox_id}/status/shutdown",
            data={
                "timeout": int(self._shutdown_timeout),
            },
        )

    def get_task_status(self, upid: str) -> TaskStatus:
        encoded_upid = urllib.parse.quote(
            upid,
            safe="",
        )

        data = self._http_client.request(
            "GET",
            f"/nodes/{self._node}/tasks/{encoded_upid}/status",
        )

        return TaskStatus(
            upid=upid,
            status=str(data["status"]),
            exitstatus=data.get("exitstatus"),
        )
