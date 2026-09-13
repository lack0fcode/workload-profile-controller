from unittest.mock import MagicMock, patch

from workload_profile_controller.backends.proxmox.auth import ProxmoxToken
from workload_profile_controller.backends.proxmox.config import ProxmoxConfig
from workload_profile_controller.backends.proxmox.errors import ProxmoxHttpError
from workload_profile_controller.backends.proxmox.http_client import ProxmoxHttpClient


def make_config(
    verify_tls=True,
    ca_file=None,
    tls_server_name="proxmox.example",
    timeout=5.0,
):
    return ProxmoxConfig(
        host="192.0.2.10",
        node="pve-node-01",
        user="controller@pve",
        token_name="controller",
        token_secret="secret",
        verify_tls=verify_tls,
        ca_file=ca_file,
        tls_server_name=tls_server_name,
        timeout=timeout,
    )


def make_token():
    return ProxmoxToken(
        user="controller@pve",
        token_name="controller",
        secret="secret",
    )


def make_connection(response_data):
    connection = MagicMock()
    response = MagicMock()

    response.status = 200
    response.reason = "OK"

    response.read.return_value = (
        __import__("json")
        .dumps({"data": response_data})
        .encode("utf-8")
    )

    connection.getresponse.return_value = response

    return connection


def test_http_client_builds_get_request():
    config = make_config()
    token = make_token()

    client = ProxmoxHttpClient(
        config=config,
        token=token,
    )

    connection = make_connection(
        {"status": "running"}
    )

    with patch(
        "workload_profile_controller.backends.proxmox.http_client._ProxmoxHTTPSConnection",
        return_value=connection,
    ) as connection_class:
        result = client.request(
            "GET",
            "/nodes/pve-node-01/qemu/169/status/current",
        )

    assert result == {"status": "running"}

    connection_class.assert_called_once_with(
        connect_host="192.0.2.10",
        tls_server_name="proxmox.example",
        context=connection_class.call_args.kwargs["context"],
        timeout=5.0,
    )

    connection.request.assert_called_once_with(
        "GET",
        "/api2/json/nodes/pve-node-01/qemu/169/status/current",
        body=None,
        headers={
            "Authorization": (
                "PVEAPIToken=controller@pve!controller=secret"
            ),
        },
    )


def test_http_client_sends_post_data():
    config = make_config()
    token = make_token()

    client = ProxmoxHttpClient(
        config=config,
        token=token,
    )

    connection = make_connection("UPID:test")

    with patch(
        "workload_profile_controller.backends.proxmox.http_client._ProxmoxHTTPSConnection",
        return_value=connection,
    ):
        result = client.request(
            "POST",
            "/nodes/pve-node-01/qemu/169/status/start",
            data={"test": "value"},
        )

    assert result == "UPID:test"

    connection.request.assert_called_once_with(
        "POST",
        "/api2/json/nodes/pve-node-01/qemu/169/status/start",
        body=b"test=value",
        headers={
            "Authorization": (
                "PVEAPIToken=controller@pve!controller=secret"
            ),
        },
    )


def test_http_client_uses_tls_verification_by_default():
    config = make_config(
        ca_file="/tmp/proxmox-ca.pem",
    )
    token = make_token()

    client = ProxmoxHttpClient(
        config=config,
        token=token,
    )

    connection = make_connection(None)

    with patch(
        "workload_profile_controller.backends.proxmox.http_client.ssl.create_default_context"
    ) as create_context:
        create_context.return_value = MagicMock()

        with patch(
            "workload_profile_controller.backends.proxmox.http_client._ProxmoxHTTPSConnection",
            return_value=connection,
        ):
            client.request("GET", "/test")

    create_context.assert_called_once_with(
        cafile="/tmp/proxmox-ca.pem",
    )


def test_http_client_can_disable_tls_verification_explicitly():
    config = make_config(
        verify_tls=False,
    )
    token = make_token()

    client = ProxmoxHttpClient(
        config=config,
        token=token,
    )

    connection = make_connection(None)

    with patch(
        "workload_profile_controller.backends.proxmox.http_client.ssl._create_unverified_context"
    ) as create_context:
        create_context.return_value = MagicMock()

        with patch(
            "workload_profile_controller.backends.proxmox.http_client._ProxmoxHTTPSConnection",
            return_value=connection,
        ):
            client.request("GET", "/test")

    create_context.assert_called_once()


def test_http_client_uses_configured_timeout():
    config = make_config(
        timeout=12.5,
    )
    token = make_token()

    client = ProxmoxHttpClient(
        config=config,
        token=token,
    )

    connection = make_connection(None)

    with patch(
        "workload_profile_controller.backends.proxmox.http_client._ProxmoxHTTPSConnection",
        return_value=connection,
    ) as connection_class:
        client.request("GET", "/test")

    assert connection_class.call_args.kwargs["timeout"] == 12.5


def test_http_client_uses_tls_server_name():
    config = make_config(
        tls_server_name="pve-node-01.example.test",
    )
    token = make_token()

    client = ProxmoxHttpClient(
        config=config,
        token=token,
    )

    connection = make_connection(None)

    with patch(
        "workload_profile_controller.backends.proxmox.http_client._ProxmoxHTTPSConnection",
        return_value=connection,
    ) as connection_class:
        client.request("GET", "/test")

    assert (
        connection_class.call_args.kwargs["connect_host"]
        == "192.0.2.10"
    )

    assert (
        connection_class.call_args.kwargs["tls_server_name"]
        == "pve-node-01.example.test"
    )

def test_http_client_raises_error_for_http_failure():
    config = make_config()
    token = make_token()

    client = ProxmoxHttpClient(
        config=config,
        token=token,
    )

    connection = make_connection(None)
    response = connection.getresponse.return_value

    response.status = 401
    response.reason = "Authentication failed!"

    with patch(
        "workload_profile_controller.backends.proxmox.http_client._ProxmoxHTTPSConnection",
        return_value=connection,
    ):
        try:
            client.request("GET", "/test")
        except ProxmoxHttpError as error:
            assert error.status_code == 401
            assert error.reason == "Authentication failed!"
        else:
            raise AssertionError(
                "Expected ProxmoxHttpError"
            )

def test_proxmox_https_connection_uses_port_8006():
    from workload_profile_controller.backends.proxmox.http_client import (
        _ProxmoxHTTPSConnection,
    )

    context = MagicMock()

    connection = _ProxmoxHTTPSConnection(
        connect_host="192.0.2.10",
        tls_server_name="pve-node-01.example.test",
        context=context,
        timeout=5.0,
    )

    assert connection.port == 8006