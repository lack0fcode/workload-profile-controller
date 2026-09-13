import http.client
import json
import socket
import ssl
import urllib.parse
from collections.abc import Mapping
from typing import Any

from .auth import ProxmoxToken
from .config import ProxmoxConfig
from .errors import ProxmoxHttpError


class _ProxmoxHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        connect_host: str,
        tls_server_name: str | None,
        context: ssl.SSLContext,
        timeout: float,
    ):
        super().__init__(
            host=connect_host,
            port=8006,
            timeout=timeout,
            context=context,
        )

        self._tls_server_name = tls_server_name

    def connect(self):
        self.sock = socket.create_connection(
            (self.host, self.port),
            self.timeout,
        )

        self.sock = self._context.wrap_socket(
            self.sock,
            server_hostname=self._tls_server_name or self.host,
        )


class ProxmoxHttpClient:
    def __init__(
        self,
        config: ProxmoxConfig,
        token: ProxmoxToken,
    ):
        self._config = config
        self._token = token

    def request(
        self,
        method: str,
        path: str,
        data: Mapping[str, Any] | None = None,
    ) -> Any:
        body = None

        if data is not None:
            body = urllib.parse.urlencode(data).encode("utf-8")

        context = self._create_ssl_context()

        connection = _ProxmoxHTTPSConnection(
            connect_host=self._config.host,
            tls_server_name=self._config.tls_server_name,
            context=context,
            timeout=self._config.timeout,
        )

        try:
            connection.request(
                method,
                f"/api2/json{path}",
                body=body,
                headers={
                    "Authorization": (
                        self._token.authorization_header()
                    ),
                },
            )

            response = connection.getresponse()
            if response.status < 200 or response.status >= 300:
                reason = response.reason or "Unknown error"
                response.read()

                raise ProxmoxHttpError(
                    status_code=response.status,
                    reason=reason,
                )

            payload = json.load(response)

            return payload["data"]

        finally:
            connection.close()

    def _create_ssl_context(self) -> ssl.SSLContext:
        if self._config.verify_tls:
            return ssl.create_default_context(
                cafile=self._config.ca_file,
            )

        return ssl._create_unverified_context()