#!/usr/bin/python
import re

from ansible.module_utils.basic import AnsibleModule

CRITICAL_STOPS = [
    "6_1_24_11",  # Required for MongoDB 5.0 migration
    "7_0_13_11",  # Required for breaking changes in 7.1+
]

# Valid version is represented as a tuple of 4 integers - (major, minor, patch, build)
Version = tuple[int, int, int, int]

def parse_version(version_str) -> Version:
    version_pattern = r'^(\d+)_(\d+)_(\d+)_(\d+)$'
    match = re.match(version_pattern, version_str)
    if not match:
        raise ValueError(f"Version '{version_str}' does not match required format X.Y.Z.B")

    major, minor, patch, build = (int(part) for part in match.groups())
    return major, minor, patch, build


def is_upgrade(current_version: Version, target_version: Version) -> bool:
    return current_version < target_version

def get_required_stops(current_version: Version, target_version: Version) -> list[str]:
    required_stops = [stop for stop in CRITICAL_STOPS if current_version < parse_version(stop) < target_version]
    return required_stops

def run(module: AnsibleModule):
    results = {
        "check_name": "critical stops in the upgrade path",
    }
    try:
        current_version_str = module.params["current_version"]
        target_version_str = module.params["target_version"]

        current_version = parse_version(current_version_str)
        target_version = parse_version(target_version_str)

        if not is_upgrade(current_version, target_version):
            module.exit_json(
                **results,
                status="failed",
                check_errors=f"Target version {target_version_str} must be greater than current version {current_version_str}",
                check_details={"details": "Please provide a valid upgrade path where target version is newer than current version"}
            )

        required_stops = get_required_stops(current_version, target_version)
        if required_stops:
            module.exit_json(
                **results,
                status="failed",
                check_errors=f"Upgrade path from {current_version} to {target_version} requires intermediate stops at: {', '.join(required_stops)}",
                check_details={"details": "Please upgrade to required intermediate versions before upgrading to the target version"}
            )
        else:
            module.exit_json(
                **results,
                status="success",
                check_details={"details": f"Upgrade path from {current_version} to {target_version} is valid with no required intermediate stops"}
            )
    except Exception as e:
        module.exit_json(
            **results,
            status="error",
            check_errors=str(e),
            check_details={"details": "Unexpected error during check execution"}
        )


def main():
    module_args = dict(
        current_version=dict(type="str", required=True),
        target_version=dict(type="str", required=True),
    )

    run(AnsibleModule(argument_spec=module_args))



if __name__ == '__main__':
    main()

