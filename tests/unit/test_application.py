from unittest.mock import Mock, patch

from workload_profile_controller.application import create_controller
from workload_profile_controller.config import Config
from workload_profile_controller.controller import Controller


def test_create_controller_builds_application():
    config = Mock(spec=Config)
    backend = Mock()

    with patch(
        "workload_profile_controller.application.load_config",
        return_value=config,
    ) as load_config, patch(
        "workload_profile_controller.application.create_proxmox_backend",
        return_value=backend,
    ) as create_backend:
        controller = create_controller(
            "config/example.yaml"
        )

    assert isinstance(controller, Controller)

    load_config.assert_called_once_with(
        "config/example.yaml"
    )

    create_backend.assert_called_once_with()

    assert controller._config is config
    assert controller._backend is backend
