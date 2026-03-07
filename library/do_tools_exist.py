import shutil

from ansible.module_utils.basic import AnsibleModule


def run(module: AnsibleModule):
    results = {
        "check_name": "required tools exist",
    }
    details = {}
    try:
        tool_list = module.params["tool_list"]
        details["all_tools"] = tool_list

        missing_tools = []
        for tool in tool_list:
            # shutil.which is marked deprecated only for PathLike on Windows <3.12.
            # We pass a string and run on Linux, so this is safe.
            # noinspection PyDeprecation
            if not shutil.which(tool):   # pylint: disable=deprecated-method
                missing_tools.append(tool)

        if missing_tools:
            details["missing_tools"] = missing_tools
            module.exit_json(
                **results,
                status="failed",
                check_errors=f"Missing required tools: {', '.join(missing_tools)}",
                check_details=details
            )
        else:
            module.exit_json(
                **results,
                status="success",
                check_details=details
            )
    except Exception as e:
        details["check_errors"] = str(e)
        module.exit_json(
            **results,
            status="error",
            check_errors=str(e),
            check_details=details
        )

def main():
    module_args = dict(
        tool_list=dict(type="list", elements="str", required=True),
    )

    run(AnsibleModule(argument_spec=module_args))


if __name__ == '__main__':
    main()