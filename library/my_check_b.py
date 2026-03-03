#!/usr/bin/python
"""
Custom Ansible module: my_check_b
This is a stub module for check B
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            param1=dict(required=True, type='str'),
            param2=dict(required=True, type='str'),
        )
    )

    # Stub implementation
    results = {
        "check_name": "my_check_b",
        "status": "success",
        "check_errors": "Terrible errors found",
        "check_details": {
            "name": "Check B",
            "status": "passed",
            "details": f"Received param1={module.params['param1']} and param2={module.params['param2']}"
        }
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()

