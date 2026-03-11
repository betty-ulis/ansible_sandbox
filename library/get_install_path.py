#!/usr/bin/env python

import json
import os
import re
import subprocess
from functools import partial
from pathlib import Path
from typing import Callable

from ansible.module_utils.basic import AnsibleModule

UNKNOWN = "N/A"

INSTALL_PATH_KEY = "install_path"
CORTEX_PATH_KEY = "cortex_path"
AXONIUS_CONF_PATH_KEY = "axonius_conf"

CONFIG_FILE = "conf.json"
CONFIG_DIR = "config"
CORTEX_DIR = "cortex"
DEFAULT_CONF_PATH = Path("/etc/axonius")

Resolver = Callable[[], str|None]


def os_path_resolver(path: Path) -> str|None:
    """Check if the specified path exists and return it as a string if it does.
    Args:
        path (Path): The path to check for existence
    Returns:
        str|None: The path as a string if it exists, otherwise None
    """
    return str(path) if path.exists() else None


def docker_path_resolver() -> str|None:
    """Check for Docker-based configuration path by running 'docker info'
    and inferring the config path from DockerRootDir.
    Returns:
        str|None: The inferred configuration path if found and valid, otherwise None
    """
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{ .DockerRootDir }}"],
            capture_output=True,
            text=True
        )
        docker_root = result.stdout.strip()
        conf_path = Path(docker_root).parent / CONFIG_DIR / CONFIG_FILE
        return str(conf_path) if conf_path.exists() else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def crontab_path_resolver() -> str|None:
    """Check for crontab-based configuration path
    by looking for machine_boot.sh and inferring the config path from it.
    Returns:
        str|None: The inferred configuration path if found and valid, otherwise None
    """

    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
        )
        crontab_entries = result.stdout
        match = re.search(r"/.*?machine_boot\.sh", crontab_entries)
        if match:
            machine_boot_path = match.group(0)
            conf_path = machine_boot_path.replace(
                "f/{CORTEX_DIR}/machine_boot.sh", f"/{CONFIG_DIR}/{CONFIG_FILE}"
            )
            path = Path(conf_path)
            return str(path) if path.exists() else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def apply_resolvers(resolvers: list[Resolver]) -> str|None:
    """Apply a list of resolvers and return the first valid path found.
    Args:
        resolvers (list[Resolver]): List of resolver functions to apply
    Returns:
        str|None: The first valid path found by the resolvers, or None if none are valid
    """
    for resolver in resolvers:
        result = resolver()
        if result:
            return result
    return None


def create_custom_paths_list(custom_paths_str: list[str]) -> list[Path]:
    """Convert a list of custom path strings into a list of Path objects,
    appending CONFIG_FILE if the path is a directory.
    Args:
        custom_paths_str (list[str]): List of custom path strings
    Returns:
        list[Path]: List of Path objects representing the custom paths to check
    """
    custom_paths = []
    for path_str in custom_paths_str:
        path = Path(path_str.strip())
        if path.is_dir():
            custom_paths.append(path / CONFIG_FILE)
        else:
            custom_paths.append(path)
    return custom_paths


def load_config(conf_path) -> dict:
    """Load and parse Axonius configuration file
    Args:
        conf_path (str): Path to the configuration file
    Returns:
        dict: Parsed configuration data
    Raises:
        ValueError: If the file cannot be read or parsed
    """
    try:
        with open(conf_path, "r") as f:
            config = json.load(f)
        return config
    except (IOError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to load configuration from {conf_path}: {e}")


def run(module: AnsibleModule) -> None:
    """Main execution function for the Ansible module."""
    results = {
        INSTALL_PATH_KEY: UNKNOWN,
        CORTEX_PATH_KEY: UNKNOWN,
        AXONIUS_CONF_PATH_KEY: UNKNOWN,
    }

    try:
        custom_paths_str = module.params["custom_paths"]
        custom_paths = create_custom_paths_list(custom_paths_str)

        if not all(path.is_absolute() for path in custom_paths):
            module.fail_json(
                **results,
                msg="All custom paths must be absolute paths.",
                relative_paths = [str(path) for path in custom_paths if not path.is_absolute()]
            )
        if DEFAULT_CONF_PATH not in custom_paths:
            custom_paths.append(DEFAULT_CONF_PATH)

        resolvers: list[Resolver] = [
            *[partial(os_path_resolver, path) for path in custom_paths],
            docker_path_resolver,
            crontab_path_resolver,
        ]
        conf_path = apply_resolvers(resolvers)
        if not conf_path:
            module.fail_json(
                **results,
                msg="No valid configuration path found.",
            )

        results[AXONIUS_CONF_PATH_KEY] = conf_path
        try:
            config = load_config(conf_path)
            results[INSTALL_PATH_KEY] = config["install_path"]
            results[CORTEX_PATH_KEY] = os.path.join(results[CORTEX_PATH_KEY], CORTEX_DIR)
        except ValueError as e:
            module.fail_json(
                **results,
                msg=str(e)
            )

        module.exit_json(
            **results,
            changed=False
        )

    except Exception as e:
        module.fail_json(
            **results,
            msg=f"Error processing input parameters: {str(e)}"
        )



def main() -> None:
    """Define module arguments and run the main function."""
    module_args = dict(
        custom_paths=dict(type="list", elements="str", required=False, default=[]),
    )

    run(AnsibleModule(argument_spec=module_args))


if __name__ == "__main__":
    main()
