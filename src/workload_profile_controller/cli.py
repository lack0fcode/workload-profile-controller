import argparse

from .application import create_controller
from .config_loader import load_config


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wpc",
        description="Safe and configurable workload profile controller.",
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to the profile configuration file.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "profiles",
        help="List configured profiles.",
    )

    subparsers.add_parser(
        "status",
        help="Show the current resource status.",
    )

    plan_parser = subparsers.add_parser(
    "plan",
    help="Plan a transition without changing resources.",
    )

    plan_parser.add_argument(
    "target_profile",
    help="Target profile to plan.",
    )

    transition_parser = subparsers.add_parser(
        "transition",
        help="Transition to a configured profile.",
    )

    transition_parser.add_argument(
        "target_profile",
        help="Target profile to transition to.",
    )

    return parser


def main(argv=None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "profiles":
        config = load_config(args.config)

        for profile in config.profiles.values():
            print(
                f"{profile.name}\t{profile.description}"
            )

        return 0

    if args.command == "status":
        controller = create_controller(args.config)
        statuses = controller.get_resource_statuses()

        for resource_id, status in statuses.items():
            print(
                f"{resource_id}\t{status.value}"
            )

        return 0

    if args.command == "plan":
        controller = create_controller(args.config)

        current_profile = controller.reconcile()
        target_profile = args.target_profile

        if not controller.has_profile(target_profile):
            parser.error(
                f"Unknown profile: {target_profile}"
            )

        plan = controller.build_transition_plan(
            current_profile,
            target_profile,
        )

        print(f"Current profile: {current_profile}")
        print(f"Target profile: {target_profile}")
        print()
        print("Plan:")

        if not plan.actions:
            print("  no changes required")
        else:
            for action in plan.actions:
                print(
                    f"  {action.action.value} "
                    f"{action.resource_id}"
                )

        print()
        print("No changes were made.")

        return 0

    if args.command == "transition":
        controller = create_controller(args.config)

        current_profile = controller.reconcile()
        target_profile = args.target_profile

        if not controller.has_profile(target_profile):
            parser.error(
                f"Unknown profile: {target_profile}"
            )

        if current_profile == target_profile:
            print(
                f"Already in profile: {target_profile}"
            )
            return 0

        print(
            f"Transitioning from "
            f"{current_profile} to {target_profile}..."
        )

        controller.transition(
            current_profile,
            target_profile,
        )

        print(
            f"Transition completed: {target_profile}"
        )

        return 0

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())