from .config import Config


def validate_config(config: Config) -> None:
    # R-01 — At least one resource
    if not config.resources:
        raise ValueError("At least one resource is required")

    # R-02 — Resource identity
    for resource_id, resource in config.resources.items():
        if not isinstance(resource_id, str) or not resource_id.strip():
            raise ValueError("Resource ID must not be empty")

        if not isinstance(resource.name, str) or not resource.name.strip():
            raise ValueError(
                f"Resource name must not be empty: {resource_id}"
            )

    # At least one profile
    if not config.profiles:
        raise ValueError("At least one profile is required")

    managed_resources = set(config.resources)

    # Validate every profile
    for profile_name, profile in config.profiles.items():
        # R-03 — Profile name must match dictionary key
        if profile.name != profile_name:
            raise ValueError(
                f"Profile name mismatch: key={profile_name}, "
                f"name={profile.name}"
            )

        running = profile.running
        stopped = profile.stopped

        # R-04 — All referenced resources must exist
        referenced_resources = set(running) | set(stopped)

        unknown_resources = referenced_resources - managed_resources

        if unknown_resources:
            raise ValueError(
                f"Profile {profile_name} references unknown resources: "
                f"{sorted(unknown_resources)}"
            )

        # R-05 — Mutual exclusivity
        conflicting_resources = set(running) & set(stopped)

        if conflicting_resources:
            raise ValueError(
                f"Profile {profile_name} has resources in both states: "
                f"{sorted(conflicting_resources)}"
            )

        # R-06 — No duplicates
        if len(running) != len(set(running)):
            raise ValueError(
                f"Profile {profile_name} contains duplicate resources in running"
            )

        if len(stopped) != len(set(stopped)):
            raise ValueError(
                f"Profile {profile_name} contains duplicate resources in stopped"
            )

        # R-07 — Exactly one state per managed resource
        if referenced_resources != managed_resources:
            missing_resources = managed_resources - referenced_resources

            if missing_resources:
                raise ValueError(
                    f"Profile {profile_name} does not define a state "
                    f"for resources: {sorted(missing_resources)}"
                )

        # R-10 — No empty profile
        if not running and not stopped:
            raise ValueError(
                f"Profile {profile_name} cannot be empty"
            )

    # R-08 — Same resource universe across all profiles
    profile_universes = {
        profile_name: set(profile.running) | set(profile.stopped)
        for profile_name, profile in config.profiles.items()
    }

    universes = list(profile_universes.values())
    reference_universe = universes[0]

    for profile_name, universe in profile_universes.items():
        if universe != reference_universe:
            raise ValueError(
                f"Profile {profile_name} manages a different resource universe"
            )

    # R-09 — Complete deterministic state
    for profile_name, profile in config.profiles.items():
        universe = set(profile.running) | set(profile.stopped)

        if universe != managed_resources:
            raise ValueError(
                f"Profile {profile_name} does not define a complete state"
            )