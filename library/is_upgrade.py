#!/usr/bin/python
"""
Custom Ansible module: my_check_b
This is a stub module for check B
"""

from ansible.module_utils.basic import AnsibleModule

def run(module: AnsibleModule):
    results = {
        "check_name": "is_upgrade",
    }
    try:
        current_version = module.params["current_version"]
        target_version = module.params["target_version"]
        # Validate version formats
        current_ver_parsed = parse_version(current_version)
        target_ver_parsed = parse_version(target_version)
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

