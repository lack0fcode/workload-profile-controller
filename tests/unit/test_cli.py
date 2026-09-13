from unittest.mock import Mock, patch

from workload_profile_controller.backend import ResourceStatus
from workload_profile_controller.cli import main


def test_status_command(capsys):
    controller = Mock()

    controller.get_resource_statuses.return_value = {
        "monitoring": ResourceStatus.RUNNING,
        "application": ResourceStatus.RUNNING,
        "compute": ResourceStatus.STOPPED,
    }

    with patch(
        "workload_profile_controller.cli.create_controller",
        return_value=controller,
    ) as create_controller:
        exit_code = main([
            "--config",
            "config/examples/config.example.yaml",
            "status",
        ])

    captured = capsys.readouterr()

    assert exit_code == 0

    assert captured.out == (
        "monitoring\trunning\n"
        "application\trunning\n"
        "compute\tstopped\n"
    )

    create_controller.assert_called_once_with(
        "config/examples/config.example.yaml"
    )

    controller.get_resource_statuses.assert_called_once_with()

def test_transition_command(capsys):
    controller = Mock()

    controller.reconcile.return_value = "profile2"
    controller.has_profile.return_value = True

    with patch(
        "workload_profile_controller.cli.create_controller",
        return_value=controller,
    ) as create_controller:
        exit_code = main([
            "--config",
            "config/examples/config.example.yaml",
            "transition",
            "profile1",
        ])

    captured = capsys.readouterr()

    assert exit_code == 0

    assert captured.out == (
        "Transitioning from profile2 to profile1...\n"
        "Transition completed: profile1\n"
    )

    create_controller.assert_called_once_with(
        "config/examples/config.example.yaml"
    )

    controller.reconcile.assert_called_once_with()

    controller.has_profile.assert_called_once_with(
        "profile1"
    )

    controller.transition.assert_called_once_with(
        "profile2",
        "profile1",
    )


def test_transition_command_already_in_target_profile(capsys):
    controller = Mock()

    controller.reconcile.return_value = "profile2"

    with patch(
        "workload_profile_controller.cli.create_controller",
        return_value=controller,
    ):
        exit_code = main([
            "--config",
            "config/examples/config.example.yaml",
            "transition",
            "profile2",
        ])

    captured = capsys.readouterr()

    assert exit_code == 0

    assert captured.out == (
        "Already in profile: profile2\n"
    )

    controller.reconcile.assert_called_once_with()
    controller.transition.assert_not_called()


def test_transition_command_rejects_unknown_profile(capsys):
    controller = Mock()

    controller.reconcile.return_value = "profile2"
    controller.has_profile.return_value = False

    with patch(
        "workload_profile_controller.cli.create_controller",
        return_value=controller,
    ):
        try:
            main([
                "--config",
                "config/examples/config.example.yaml",
                "transition",
                "profile99",
            ])
        except SystemExit as error:
            assert error.code == 2
        else:
            raise AssertionError(
                "Expected SystemExit"
            )

    captured = capsys.readouterr()

    assert "Unknown profile: profile99" in captured.err

    controller.reconcile.assert_called_once_with()

    controller.has_profile.assert_called_once_with(
        "profile99"
    )

    controller.transition.assert_not_called()