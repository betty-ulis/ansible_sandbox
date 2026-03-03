import re

from ansible.module_utils.basic import AnsibleModule

version_pattern = r'^(\d+)_(\d+)_(\d+)_(\d+)$'


def run(module: AnsibleModule):

    results = {
        "check_name": "validate_version",
    }

    try:
        version = module.params["version"]
        match = re.match(version_pattern, version)
        if not match:
            module.exit_json(
                **results,
                status="failed",
                check_errors=f"Version '{version}' does not match required format X.Y.Z.B",
                check_details={"details": "Version must be in format major.minor.patch.build with numeric values"}
            )
        module.exit_json(
            **results,
            status="success",
            check_details={"details": f"Version '{version}' is valid"}
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
        version=dict(type="str", required=True),
    )

    run(AnsibleModule(argument_spec=module_args))



if __name__ == '__main__':
    main()
