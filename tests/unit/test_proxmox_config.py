from workload_profile_controller.backends.proxmox.config import ProxmoxConfig


def test_proxmox_config_can_be_created():
    config = ProxmoxConfig(
        host="192.0.2.10",
        node="pve-node-01",
        user="root@pam",
        token_name="controller",
        token_secret="secret",
    )

    assert config.host == "192.0.2.10"
    assert config.node == "pve-node-01"
    assert config.user == "root@pam"
    assert config.token_name == "controller"
    assert config.token_secret == "secret"
    assert config.verify_tls is True
    assert config.timeout == 5.0


def test_proxmox_config_accepts_custom_connection_options():
    config = ProxmoxConfig(
        host="proxmox.example.com",
        node="node01",
        user="controller@pam",
        token_name="api",
        token_secret="secret",
        verify_tls=False,
        timeout=10.0,
    )

    assert config.verify_tls is False
    assert config.timeout == 10.0
