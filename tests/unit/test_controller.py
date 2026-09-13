from unittest.mock import Mock

import pytest

from workload_profile_controller.backend import ResourceStatus
from workload_profile_controller.config import (
    Config,
    ProfileConfig,
    ResourceConfig,
)
from workload_profile_controller.controller import Controller, ControllerState


def make_config():
    return Config(
        resources={
            "monitoring": ResourceConfig(
                name="monitoring",
                description="Monitoring workload",
            ),
            "compute": ResourceConfig(
                name="compute",
                description="Compute workload",
            ),
            "application": ResourceConfig(
                name="application",
                description="Application workload",
            ),
        },
        profiles={
            "profile1": ProfileConfig(
                name="profile1",
                description="Normal operation",
                running=("monitoring", "application"),
                stopped=("compute",),
            ),
            "profile2": ProfileConfig(
                name="profile2",
                description="Compute workload",
                running=("compute",),
                stopped=("monitoring", "application"),
            ),
        },
    )


class FakeBackend:
    def __init__(self):
        self.resources = {
            "monitoring": ResourceStatus.RUNNING,
            "application": ResourceStatus.RUNNING,
            "compute": ResourceStatus.STOPPED,
        }

    def get_status(self, resource_id: str) -> ResourceStatus:
        return self.resources[resource_id]

    def start(self, resource_id: str) -> None:
        self.resources[resource_id] = ResourceStatus.RUNNING

    def stop(self, resource_id: str) -> None:
        self.resources[resource_id] = ResourceStatus.STOPPED


def test_controller_can_be_created():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)

    assert controller is not None


def test_controller_can_get_profile():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)

    profile = controller.get_profile("profile1")

    assert profile.name == "profile1"
    assert profile.running == ("monitoring", "application")
    assert profile.stopped == ("compute",)


def test_controller_can_build_transition_plan():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)

    plan = controller.build_transition_plan("profile1", "profile2")

    assert [action.resource_id for action in plan.actions] == [
        "monitoring",
        "application",
        "compute",
    ]


def test_controller_accepts_generic_backend():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)

    assert backend.get_status("compute") == ResourceStatus.STOPPED
    assert backend.get_status("monitoring") == ResourceStatus.RUNNING

def test_controller_can_execute_transition():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)

    controller.transition("profile1", "profile2")

    assert backend.get_status("monitoring") == ResourceStatus.STOPPED
    assert backend.get_status("application") == ResourceStatus.STOPPED
    assert backend.get_status("compute") == ResourceStatus.RUNNING

class FailingBackend(FakeBackend):
    def stop(self, resource_id: str) -> None:
        pass

def test_controller_fails_if_resource_does_not_stop():
    config = make_config()
    backend = FailingBackend()

    controller = Controller(config, backend)

    with pytest.raises(RuntimeError, match="Resource did not stop"):
        controller.transition("profile1", "profile2")

class TrackingFailingBackend(FakeBackend):
    def __init__(self):
        super().__init__()
        self.actions = []

    def stop(self, resource_id: str) -> None:
        self.actions.append(("stop", resource_id))
        raise RuntimeError("backend failure")


def test_controller_stops_after_first_failed_action():
    config = make_config()
    backend = TrackingFailingBackend()

    controller = Controller(config, backend)

    with pytest.raises(RuntimeError, match="backend failure"):
        controller.transition("profile1", "profile2")

    assert backend.actions == [
        ("stop", "monitoring"),
    ]

class StartFailingBackend(FakeBackend):
    def __init__(self):
        super().__init__()
        self.actions = []

    def stop(self, resource_id: str) -> None:
        self.actions.append(("stop", resource_id))
        super().stop(resource_id)

    def start(self, resource_id: str) -> None:
        self.actions.append(("start", resource_id))
        raise RuntimeError("backend start failure")


def test_controller_fails_if_resource_does_not_start():
    config = make_config()
    backend = StartFailingBackend()

    controller = Controller(config, backend)

    with pytest.raises(RuntimeError, match="backend start failure"):
        controller.transition("profile1", "profile2")

    assert backend.actions == [
        ("stop", "monitoring"),
        ("stop", "application"),
        ("start", "compute"),
    ]

def test_controller_rejects_transition_if_source_profile_is_not_active():
    config = make_config()
    backend = FakeBackend()

    backend.resources["monitoring"] = ResourceStatus.STOPPED

    controller = Controller(config, backend)

    with pytest.raises(RuntimeError, match="Source profile is not active"):
        controller.transition("profile1", "profile2")

    assert backend.get_status("monitoring") == ResourceStatus.STOPPED
    assert backend.get_status("application") == ResourceStatus.RUNNING
    assert backend.get_status("compute") == ResourceStatus.STOPPED
    assert controller.state == ControllerState.IDLE

class TrackingBackend(FakeBackend):
    def __init__(self):
        super().__init__()
        self.actions = []

    def start(self, resource_id: str) -> None:
        self.actions.append(("start", resource_id))
        super().start(resource_id)

    def stop(self, resource_id: str) -> None:
        self.actions.append(("stop", resource_id))
        super().stop(resource_id)


def test_controller_does_not_mutate_backend_when_source_profile_is_invalid():
    config = make_config()
    backend = TrackingBackend()

    backend.resources["monitoring"] = ResourceStatus.STOPPED

    controller = Controller(config, backend)

    with pytest.raises(RuntimeError, match="Source profile is not active"):
        controller.transition("profile1", "profile2")

    assert backend.actions == []

class InconsistentBackend(FakeBackend):
    def start(self, resource_id: str) -> None:
        super().start(resource_id)

        if resource_id == "compute":
            self.resources["application"] = ResourceStatus.RUNNING

def test_controller_rejects_invalid_final_state():
    config = make_config()
    backend = InconsistentBackend()

    controller = Controller(config, backend)

    with pytest.raises(RuntimeError, match="Target profile is not active"):
        controller.transition("profile1", "profile2")

def test_reconcile_identifies_active_profile():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)

    profile = controller.reconcile()

    assert profile == "profile1"
    assert controller.state == ControllerState.IDLE

def test_reconcile_rejects_unknown_resource_state():
    config = make_config()
    backend = FakeBackend()

    backend.resources["monitoring"] = ResourceStatus.STOPPED

    controller = Controller(config, backend)

    with pytest.raises(
        RuntimeError,
        match="Current resource state does not match any profile",
    ):
        controller.reconcile()

    assert controller.state == ControllerState.LOCKED

def test_controller_state_contains_expected_states():
    assert ControllerState.IDLE.value == "idle"
    assert ControllerState.TRANSITIONING.value == "transitioning"
    assert ControllerState.LOCKED.value == "locked"

def test_controller_starts_in_idle_state():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)

    assert controller.state == ControllerState.IDLE

def test_controller_returns_to_idle_after_successful_transition():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)

    controller.transition("profile1", "profile2")

    assert controller.state == ControllerState.IDLE

class StateTrackingBackend(FakeBackend):
    def __init__(self):
        super().__init__()
        self.controller = None
        self.states_during_actions = []

    def stop(self, resource_id: str) -> None:
        self.states_during_actions.append(self.controller.state)
        super().stop(resource_id)

    def start(self, resource_id: str) -> None:
        self.states_during_actions.append(self.controller.state)
        super().start(resource_id)

def test_controller_enters_transitioning_state_during_transition():
    config = make_config()
    backend = StateTrackingBackend()

    controller = Controller(config, backend)
    backend.controller = controller

    controller.transition("profile1", "profile2")

    assert backend.states_during_actions
    assert all(
        state == ControllerState.TRANSITIONING
        for state in backend.states_during_actions
    )

    assert controller.state == ControllerState.IDLE

def test_controller_enters_locked_state_after_partial_transition():
    config = make_config()
    backend = StartFailingBackend()

    controller = Controller(config, backend)

    with pytest.raises(RuntimeError, match="backend start failure"):
        controller.transition("profile1", "profile2")

    assert controller.state == ControllerState.LOCKED

def test_reconcile_recovers_controller_to_idle():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)
    controller.state = ControllerState.LOCKED

    profile = controller.reconcile()

    assert profile == "profile1"
    assert controller.state == ControllerState.IDLE

def test_locked_controller_rejects_transition():
    config = make_config()
    backend = FakeBackend()

    controller = Controller(config, backend)
    controller.state = ControllerState.LOCKED

    with pytest.raises(RuntimeError, match="Controller is locked"):
        controller.transition("profile1", "profile2")

    assert backend.get_status("monitoring") == ResourceStatus.RUNNING
    assert backend.get_status("application") == ResourceStatus.RUNNING
    assert backend.get_status("compute") == ResourceStatus.STOPPED

def test_transition_does_not_mutate_when_target_resource_cannot_be_resolved():
    config = make_config()
    backend = Mock()

    backend.get_status.side_effect = [
        ResourceStatus.RUNNING,
        ResourceStatus.RUNNING,
        ResourceStatus.STOPPED,
        RuntimeError("Proxmox resource not found: compute"),
    ]

    controller = Controller(config, backend)

    with pytest.raises(RuntimeError, match="Proxmox resource not found"):
        controller.transition("profile1", "profile2")

    backend.stop.assert_not_called()
    backend.start.assert_not_called()

    assert controller.state == ControllerState.IDLE


def test_transition_validates_all_target_resources_before_mutation():
    config = make_config()
    backend = Mock()

    backend.get_status.side_effect = [
        # Source profile validation
        ResourceStatus.RUNNING,
        ResourceStatus.RUNNING,
        ResourceStatus.STOPPED,

        # Target profile resource preflight
        ResourceStatus.STOPPED,
        ResourceStatus.STOPPED,
        ResourceStatus.RUNNING,

        # Stop confirmations
        ResourceStatus.STOPPED,
        ResourceStatus.STOPPED,

        # Start confirmation
        ResourceStatus.RUNNING,

        # Final target profile validation
        ResourceStatus.RUNNING,
        ResourceStatus.STOPPED,
        ResourceStatus.STOPPED,
    ]

    controller = Controller(config, backend)

    controller.transition("profile1", "profile2")

    assert backend.stop.call_count == 2
    assert backend.start.call_count == 1

    backend.stop.assert_any_call("monitoring")
    backend.stop.assert_any_call("application")
    backend.start.assert_called_once_with("compute")

    assert controller.state == ControllerState.IDLE

def test_reconcile_does_not_mutate_backend():
    config = make_config()
    backend = TrackingBackend()

    controller = Controller(config, backend)

    profile = controller.reconcile()

    assert profile == "profile1"
    assert backend.actions == []
    assert backend.get_status("monitoring") == ResourceStatus.RUNNING
    assert backend.get_status("application") == ResourceStatus.RUNNING
    assert backend.get_status("compute") == ResourceStatus.STOPPED