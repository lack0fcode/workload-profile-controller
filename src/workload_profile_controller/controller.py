from enum import Enum

from .backend import ResourceStatus
from .policy import Policy


class ControllerState(Enum):
    IDLE = "idle"
    TRANSITIONING = "transitioning"
    LOCKED = "locked"


class Controller:
    def __init__(self, config, backend):
        self._config = config
        self._backend = backend
        self._policy = Policy(config)
        self.state = ControllerState.IDLE

    def get_profile(self, name):
        return self._policy.get_profile(name)

    def has_profile(self, name):
        return self._policy.has_profile(name)

    def build_transition_plan(self, source_profile, target_profile):
        return self._policy.build_transition_plan(
            source_profile,
            target_profile,
        )

    def transition(self, source_profile, target_profile):
        if self.state == ControllerState.LOCKED:
            raise RuntimeError("Controller is locked")

        self._validate_profile_state(source_profile)
        self._validate_profile_resources(target_profile)

        self.state = ControllerState.TRANSITIONING

        try:
            plan = self.build_transition_plan(
                source_profile,
                target_profile,
            )

            for action in plan.actions:
                if action.action.value == "stop":
                    self._backend.stop(action.resource_id)

                    status = self._backend.get_status(action.resource_id)

                    if status != ResourceStatus.STOPPED:
                        raise RuntimeError(
                            f"Resource did not stop: {action.resource_id}"
                        )

                elif action.action.value == "start":
                    self._backend.start(action.resource_id)

                    status = self._backend.get_status(action.resource_id)

                    if status != ResourceStatus.RUNNING:
                        raise RuntimeError(
                            f"Resource did not start: {action.resource_id}"
                        )

            self._validate_target_profile_state(target_profile)

            self.state = ControllerState.IDLE

        except Exception:
            self.state = ControllerState.LOCKED
            raise

    def _validate_profile_resources(self, profile_name):
        profile = self._policy.get_profile(profile_name)

        for resource_id in profile.running:
            self._backend.get_status(resource_id)

        for resource_id in profile.stopped:
            self._backend.get_status(resource_id)

    def _validate_profile_state(self, profile_name):
        profile = self._policy.get_profile(profile_name)

        for resource_id in profile.running:
            status = self._backend.get_status(resource_id)

            if status != ResourceStatus.RUNNING:
                raise RuntimeError("Source profile is not active")

        for resource_id in profile.stopped:
            status = self._backend.get_status(resource_id)

            if status != ResourceStatus.STOPPED:
                raise RuntimeError("Source profile is not active")

    def _validate_target_profile_state(self, profile_name):
        profile = self._policy.get_profile(profile_name)

        for resource_id in profile.running:
            status = self._backend.get_status(resource_id)

            if status != ResourceStatus.RUNNING:
                raise RuntimeError("Target profile is not active")

        for resource_id in profile.stopped:
            status = self._backend.get_status(resource_id)

            if status != ResourceStatus.STOPPED:
                raise RuntimeError("Target profile is not active")

    def get_resource_statuses(self):
        statuses = {}

        for resource_id in self._config.resources:
            statuses[resource_id] = self._backend.get_status(resource_id)

        return statuses

    def reconcile(self):
        for profile_name in self._policy.list_profiles():
            profile = self._policy.get_profile(profile_name)

            matches = True

            for resource_id in profile.running:
                status = self._backend.get_status(resource_id)

                if status != ResourceStatus.RUNNING:
                    matches = False
                    break

            if not matches:
                continue

            for resource_id in profile.stopped:
                status = self._backend.get_status(resource_id)

                if status != ResourceStatus.STOPPED:
                    matches = False
                    break

            if matches:
                self.state = ControllerState.IDLE
                return profile_name

        self.state = ControllerState.LOCKED

        raise RuntimeError(
            "Current resource state does not match any profile"
        )