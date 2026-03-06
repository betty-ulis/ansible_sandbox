#!/usr/bin/python3
import re
from typing import Optional

from ansible.module_utils.basic import AnsibleModule

CRITICAL_STOPS = [
    "6_1_24_11",  # Required for MongoDB 5.0 migration
    "7_0_13_11",  # Required for breaking changes in 7_1+
]

# Valid version is represented as a tuple of 4 integers - (major, minor, patch, build)
VERSION_PATTERN = r'^(\d+)_(\d+)_(\d+)_(\d+)$'
Version = tuple[int, int, int, int]

def parse_version(version_str: str) -> Optional[Version]:
    match = re.match(VERSION_PATTERN, version_str)
    if not match:
        return None
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

        details = {
            "current_version": f"Provided current version: {current_version_str}",
            "target_version": f"Provided target version: {target_version_str if target_version_str else 'Not provided'}",
        }

        current_version = parse_version(current_version_str)

        if not target_version_str:
            results["check_skipped"] = "Target version is not provided.Checking current version format only. Skipping critical stops check."

            details.update({
                "target_version_format": "Skipped due to missing target version.",
                "critical_stops": "Skipped due to missing target version."
            })

            if not current_version:
                details["current_version_format"] = f"Wrong format. Version must be in format major_minor_patch_build with numeric values."
                check_error_message = f"Current version {current_version_str} does not match required format X_Y_Z_B."
                module.exit_json(
                    **results,
                    status="failed",
                    check_errors=check_error_message,
                    check_details=details
                )
            else:
                details["current_version_format"] = f"Valid format."
                module.exit_json(
                    **results,
                    status="success",
                    check_details=details
                )

        target_version = parse_version(target_version_str)

        if not current_version or not target_version:
            details.update({
                "current_version_format": f"Wrong format. Version must be in format major_minor_patch_build with numeric values." \
                    if not current_version else "Valid format.",
                "target_version_format": f"Wrong format. Version must be in format major_minor_patch_build with numeric values." \
                    if not target_version else "Valid format.",
                "critical_stops": "Skipped due to invalid version format."
            })

            wrong_versions = []
            if not current_version:
                wrong_versions.append(f"current version {current_version_str}")
            if not target_version:
                wrong_versions.append(f"target version {target_version_str}")

            check_error_message = f"Invalid version format for {' and '.join(wrong_versions)}. " \
                f"Expected format is major_minor_patch_build with numeric values (e.g., 7_1_10_12)."

            check_skipped_message = "Critical stops check skipped due to invalid version format."

            module.exit_json(
                **results,
                status="failed",
                check_errors=check_error_message,
                check_skippes=check_skipped_message,
                check_details=details
            )

        details.update({
            "current_version_format": "Valid format.",
            "target_version_format": "Valid format.",
        })

        if not is_upgrade(current_version, target_version):
            details["critical_stops"] = "Irrelevant for downgrade."
            module.exit_json(
                **results,
                status="failed",
                check_errors=f"Target version {target_version_str} must be greater than current version {current_version_str}",
                check_details=details
            )

        details["stops_verified"] = f"{CRITICAL_STOPS}"

        required_stops = get_required_stops(current_version, target_version)
        if required_stops:
            details["critical_stops"] = f"Required intermediate versions {', '.join(required_stops)}"
            module.exit_json(
                **results,
                status="failed",
                check_errors=f"Upgrade path from {current_version_str} to {target_version_str} requires intermediate stops at: {', '.join(required_stops)}",
                check_details=details
            )
        else:
            details["critical_stops"] = f"Upgrade path from {current_version_str} to {target_version_str} is valid."
            module.exit_json(
                **results,
                status="success",
                check_details=details
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
        target_version=dict(type="str", required=False, default=None),
    )

    run(AnsibleModule(argument_spec=module_args))



if __name__ == '__main__':
    main()

