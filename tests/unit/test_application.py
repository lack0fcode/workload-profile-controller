from unittest.mock import Mock, patch

import pytest

from workload_profile_controller.application import create_controller
from workload_profile_controller.config import Config
from workload_profile_controller.controller import Controller


def test_create_controller_builds_proxmox_application():
    config = Mock(spec=Config)
    config.backend = "proxmox"

    backend = Mock()

    with patch(
        "workload_profile_controller.application.load_config",
        return_value=config,
    ) as load_config, patch(
        "workload_profile_controller.application.create_proxmox_backend",
        return_value=backend,
    ) as create_backend, patch(
        "workload_profile_controller.application.create_aws_backend",
    ) as create_aws_backend:
        controller = create_controller(
            "config/example.yaml"
        )

    assert isinstance(controller, Controller)

    load_config.assert_called_once_with(
        "config/example.yaml"
    )

    create_backend.assert_called_once_with()
    create_aws_backend.assert_not_called()

    assert controller._config is config
    assert controller._backend is backend


def test_create_controller_builds_aws_application():
    config = Mock(spec=Config)
    config.backend = "aws"

    backend = Mock()

    with patch(
        "workload_profile_controller.application.load_config",
        return_value=config,
    ) as load_config, patch(
        "workload_profile_controller.application.create_proxmox_backend",
    ) as create_proxmox_backend, patch(
        "workload_profile_controller.application.create_aws_backend",
        return_value=backend,
    ) as create_backend:
        controller = create_controller(
            "config/example.yaml"
        )

    assert isinstance(controller, Controller)

    load_config.assert_called_once_with(
        "config/example.yaml"
    )

    create_proxmox_backend.assert_not_called()
    create_backend.assert_called_once_with()

    assert controller._config is config
    assert controller._backend is backend


def test_create_controller_rejects_unsupported_backend():
    config = Mock(spec=Config)
    config.backend = "unknown"

    with patch(
        "workload_profile_controller.application.load_config",
        return_value=config,
    ):
        with pytest.raises(
            ValueError,
            match="Unsupported backend: unknown",
        ):
            create_controller(
                "config/example.yaml"
            )