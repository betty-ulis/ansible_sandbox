import pathlib
import sys
import os
import subprocess
from typing import NoReturn

def _set_output_var(var_name: str, var_value: str) -> None:
    """Set a GitHub Actions output variable.
    Args:
        var_name: The name of the variable to set.
        var_value: The value to set the variable to.
    """
    output_path = os.environ.get('GITHUB_OUTPUT')
    if output_path:
        with open(output_path, 'a') as f:
            f.write(f"{var_name}={var_value}\n")

def _write_summary(message: str) -> None:
    """Append a message to the GitHub step summary file.
    Args:
        message: The message to append.
    """
    summary_path = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_path:
        with open(summary_path, 'a') as f:
            f.write(message + '\n')


def _info(message: str) -> None:
    """Print a message to stdout and append to the GitHub step summary.

    Args:
        message: The message to print and append.
    """
    print(message)
    _write_summary(message)


def _fail(message: str) -> NoReturn:
    """Logs an error message.
    Then exit with status 1.
    Args:
        message: The error message to be logged.
    """
    _info(message)
    sys.exit(1)


def _load_version(version_file: str) -> str:
    """Load the version from the version file.
    Args:
        version_file: The path to the version file.
    Returns:
        The version string.
    """
    try:
        content = pathlib.Path(version_file).read_text()
        return content.strip()
    except FileNotFoundError as e:
        _fail(f"::error file={version_file}::version-check: {version_file} not found: {e}")
    except PermissionError as e:
        _fail(f"::error file={version_file}::version-check: {version_file} not readable: {e}")
    except Exception as e:
        _fail(f"::error file={version_file}::version-check: {version_file} error occurred when parsing a version file: {e}")


def _fetch_base_ref_version(base_ref: str) -> None:
    """Fetch the base ref.
    Args:
        base_ref: The base ref to fetch.
    """
    try:
        fetch_result = subprocess.run(
            ['git', 'fetch', '--depth=1', 'origin', base_ref],
            capture_output=True,
            text=True,
            check=False
        )
        if fetch_result.returncode != 0:
            raise RuntimeError(fetch_result.stderr.strip())
    except Exception as e:
        _fail(f"::error::version-check: git fetch origin {base_ref} failed: {e}")


def _load_base_ref_version(base_ref: str, version_file: str) -> str:
    """Load the version from the base ref.
    Args:
        base_ref: The base ref to compare against.
        version_file: The path to the version file.
    Returns:
        The version string.
    """
    origin_version_ref = f'origin/{base_ref}:{version_file}'

    try:
        _fetch_base_ref_version(base_ref)
        show_result = subprocess.run(
            ['git', 'show', origin_version_ref],
            capture_output=True,
            text=True,
            check=False
        )
        if show_result.returncode != 0:
            raise RuntimeError(show_result.stderr.strip())
        return show_result.stdout.strip()
    except Exception as e:
        msg = (
            f"::error::version-check: git show {origin_version_ref} failed:%0A"
            f"{e}%0A"
            f"The versions could not be compared.%0A"
        )
        _fail(msg)

def main() -> None:
    """Main entry point for the version bump enforcement script."""
    sample_file = os.environ.get("SAMPLE_FILE")
    base_ref = os.environ.get("BASE_REF")
    new_version = _load_version(sample_file)
    old_version = _load_base_ref_version(base_ref, sample_file)
    _set_output_var('version_promotion', f"{old_version}=>{new_version}")
    if new_version == old_version:
        _fail(f"::error file={sample_file}::version-check: Version did not increase. Previous (origin/{base_ref}): {old_version}. New: {new_version}. Must be strictly greater.")
    else:
        _info(f"✅ {sample_file}: version bumped {old_version} → {new_version}.")


if __name__ == "__main__":
    main()
