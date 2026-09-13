from workload_profile_controller.backends.proxmox.auth import ProxmoxToken


def test_proxmox_token_builds_authorization_header():
    token = ProxmoxToken(
        user="controller@pve",
        token_name="controller",
        secret="secret-value",
    )

    assert (
        token.authorization_header()
        == "PVEAPIToken=controller@pve!controller=secret-value"
    )


def test_proxmox_token_is_immutable():
    token = ProxmoxToken(
        user="controller@pve",
        token_name="controller",
        secret="secret-value",
    )

    try:
        token.secret = "other"
    except AttributeError:
        pass
    else:
        raise AssertionError("ProxmoxToken should be immutable")
