import pytest

from workload_profile_controller.config import (
    Config,
    ProfileConfig,
    ResourceConfig,
)
from workload_profile_controller.policy import (
    ActionType,
    Policy,
    TransitionAction,
    TransitionPlan,
)


def make_config() -> Config:

    resources = {
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
    }

    profiles = {
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
        "profile3": ProfileConfig(
            name="profile3",
            description="Maintenance",
            running=("monitoring",),
            stopped=("compute", "application"),
        ),
    }

    return Config(
        resources=resources,
        profiles=profiles,
    )


def test_policy_can_be_created():
    config = make_config()

    policy = Policy(config)

    assert policy is not None


def test_policy_returns_existing_profile():
    config = make_config()
    policy = Policy(config)

    profile = policy.get_profile("profile2")

    assert profile.name == "profile2"
    assert profile.description == "Compute workload"
    assert profile.running == ("compute",)
    assert profile.stopped == ("monitoring", "application")


def test_policy_rejects_unknown_profile():
    config = make_config()
    policy = Policy(config)

    with pytest.raises(ValueError, match="Unknown profile"):
        policy.get_profile("does-not-exist")


def test_policy_lists_profiles():
    config = make_config()
    policy = Policy(config)

    profiles = policy.list_profiles()

    assert profiles == ("profile1", "profile2", "profile3")


def test_policy_knows_if_profile_exists():
    config = make_config()
    policy = Policy(config)

    assert policy.has_profile("profile1") is True
    assert policy.has_profile("profile2") is True
    assert policy.has_profile("does-not-exist") is False


def test_policy_builds_transition_plan():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile1", "profile2")

    assert isinstance(plan, TransitionPlan)
    assert plan.actions == (
        TransitionAction(ActionType.STOP, "monitoring"),
        TransitionAction(ActionType.STOP, "application"),
        TransitionAction(ActionType.START, "compute"),
    )


def test_policy_builds_reverse_transition_plan():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile2", "profile1")

    assert plan.actions == (
        TransitionAction(ActionType.STOP, "compute"),
        TransitionAction(ActionType.START, "monitoring"),
        TransitionAction(ActionType.START, "application"),
    )


def test_policy_transition_to_same_profile_has_no_actions():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile1", "profile1")

    assert plan.actions == ()


def test_policy_rejects_unknown_source_profile():
    config = make_config()
    policy = Policy(config)

    with pytest.raises(ValueError, match="Unknown profile"):
        policy.build_transition_plan("does-not-exist", "profile2")


def test_policy_rejects_unknown_target_profile():
    config = make_config()
    policy = Policy(config)

    with pytest.raises(ValueError, match="Unknown profile"):
        policy.build_transition_plan("profile1", "does-not-exist")


def test_transition_action_can_be_created():
    action = TransitionAction(
        action=ActionType.STOP,
        resource_id="compute",
    )

    assert action.action is ActionType.STOP
    assert action.resource_id == "compute"


def test_transition_action_is_immutable():
    action = TransitionAction(
        action=ActionType.START,
        resource_id="compute",
    )

    with pytest.raises(AttributeError):
        action.resource_id = "monitoring"


def test_transition_plan_contains_ordered_actions():
    actions = (
        TransitionAction(ActionType.STOP, "monitoring"),
        TransitionAction(ActionType.STOP, "application"),
        TransitionAction(ActionType.START, "compute"),
    )

    plan = TransitionPlan(actions=actions)

    assert plan.actions == actions


def test_transition_plan_is_immutable():
    plan = TransitionPlan(
        actions=(
            TransitionAction(ActionType.STOP, "compute"),
        )
    )

    with pytest.raises(AttributeError):
        plan.actions = ()


def test_transition_plan_stops_before_starting():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile1", "profile2")

    assert plan.actions == (
        TransitionAction(ActionType.STOP, "monitoring"),
        TransitionAction(ActionType.STOP, "application"),
        TransitionAction(ActionType.START, "compute"),
    )


def test_reverse_transition_plan_stops_before_starting():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile2", "profile1")

    assert plan.actions == (
        TransitionAction(ActionType.STOP, "compute"),
        TransitionAction(ActionType.START, "monitoring"),
        TransitionAction(ActionType.START, "application"),
    )


def test_transition_plan_for_same_profile_has_no_actions():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile1", "profile1")

    assert plan.actions == ()


def test_transition_plan_profile1_to_profile3_only_stops_changed_resource():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile1", "profile3")

    assert plan.actions == (
        TransitionAction(ActionType.STOP, "application"),
    )


def test_transition_plan_profile3_to_profile2_stops_before_starting():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile3", "profile2")

    assert plan.actions == (
        TransitionAction(ActionType.STOP, "monitoring"),
        TransitionAction(ActionType.START, "compute"),
    )


def test_transition_plan_does_not_include_unchanged_resources():
    config = make_config()
    policy = Policy(config)

    plan = policy.build_transition_plan("profile1", "profile3")

    resource_ids = tuple(action.resource_id for action in plan.actions)

    assert "monitoring" not in resource_ids
    assert "compute" not in resource_ids
    assert "application" in resource_ids


def test_policy_transition_plan_always_stops_before_starting():
    config = make_config()
    policy = Policy(config)

    plans = (
        policy.build_transition_plan("profile1", "profile2"),
        policy.build_transition_plan("profile2", "profile1"),
        policy.build_transition_plan("profile2", "profile3"),
        policy.build_transition_plan("profile3", "profile2"),
    )

    for plan in plans:
        seen_start = False

        for action in plan.actions:
            if action.action is ActionType.START:
                seen_start = True

            if action.action is ActionType.STOP:
                assert not seen_start