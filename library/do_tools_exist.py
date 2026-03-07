import shutil


def run(module: AnsibleModule):
    results = {
        "check_name": "required tools exist",
    }
    try:
        tool_list = module.params["tool_list"]
        missing_tools = []
        for tool in tool_list:
            if not shutil.which(tool):
                missing_tools.append(tool)

        if missing_tools:
            module.exit_json(
                **results,
                status="failed",
                check_errors=f"Missing required tools: {', '.join(missing_tools)}",
                check_details={
                    "missing_tools": missing_tools,
                    "all_tools": tool_list
                }
            )
        else:
            module.exit_json(
                **results,
                status="success",
                check_details={
                    "all_tools": tool_list
                }
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
        tool_list=dict(type="list", elements="str", required=True),
    )

    run(AnsibleModule(argument_spec=module_args))


if __name__ == '__main__':
    main()