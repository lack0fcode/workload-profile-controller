import pytest

from workload_profile_controller.backends.proxmox.config_loader import (
    load_proxmox_config,
)


def test_load_proxmox_config_from_environment(monkeypatch):
    monkeypatch.setenv(
        "PVE_PROXMOX_HOST",
        "192.0.2.10",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_NODE",
        "pve-node-01",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_USER",
        "root@pam",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_TOKEN_NAME",
        "controller",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_TOKEN_SECRET",
        "secret",
    )

    config = load_proxmox_config()

    assert config.host == "192.0.2.10"
    assert config.node == "pve-node-01"
    assert config.user == "root@pam"
    assert config.token_name == "controller"
    assert config.token_secret == "secret"
    assert config.verify_tls is True
    assert config.timeout == 5.0


def test_load_proxmox_config_accepts_optional_environment_values(
    monkeypatch,
):
    monkeypatch.setenv(
        "PVE_PROXMOX_HOST",
        "proxmox.example.com",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_NODE",
        "node01",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_USER",
        "controller@pam",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_TOKEN_NAME",
        "api",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_TOKEN_SECRET",
        "secret",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_VERIFY_TLS",
        "false",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_TIMEOUT",
        "10.0",
    )

    config = load_proxmox_config()

    assert config.verify_tls is False
    assert config.timeout == 10.0


def test_load_proxmox_config_requires_host(monkeypatch):
    monkeypatch.delenv("PVE_PROXMOX_HOST", raising=False)
    monkeypatch.setenv(
        "PVE_PROXMOX_NODE",
        "pve-node-01",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_USER",
        "root@pam",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_TOKEN_NAME",
        "controller",
    )
    monkeypatch.setenv(
        "PVE_PROXMOX_TOKEN_SECRET",
        "secret",
    )

    with pytest.raises(KeyError):
        load_proxmox_config()
