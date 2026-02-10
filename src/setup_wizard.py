"""
First-time setup wizard for MoneyPrinterV2.

Guides new users through configuration by checking for required files,
copying example configs, and validating API keys are present.
"""

import os
import shutil
import sys
from typing import List, Tuple

from termcolor import colored

from status import error, info, question, success, warning

ROOT_DIR = os.path.dirname(sys.path[0])

# Required config files and their example sources
CONFIG_FILES = [
    (".env", ".env.example", "API keys and secrets"),
    ("config.json", "config.example.json", "Application settings"),
]

# API keys that should be configured for core functionality
REQUIRED_API_KEYS = [
    ("MISTRAL_API_KEY", "Mistral AI (text generation)", "https://console.mistral.ai/"),
]

OPTIONAL_API_KEYS = [
    ("VENICE_API_KEY", "Venice AI (image generation)", "https://venice.ai/"),
    ("ASSEMBLYAI_API_KEY", "AssemblyAI (subtitle generation)", "https://www.assemblyai.com/"),
]


def _file_exists(filename: str) -> bool:
    """Check if a file exists in the project root."""
    return os.path.exists(os.path.join(ROOT_DIR, filename))


def _copy_example_file(target: str, source: str) -> bool:
    """
    Copy an example file to create the target config file.

    Args:
        target: Target filename (e.g., ".env")
        source: Source example filename (e.g., ".env.example")

    Returns:
        True if file was copied successfully
    """
    source_path = os.path.join(ROOT_DIR, source)
    target_path = os.path.join(ROOT_DIR, target)

    if not os.path.exists(source_path):
        error(f"  Example file not found: {source}")
        return False

    try:
        shutil.copy2(source_path, target_path)
        success(f"  Created {target} from {source}")
        return True
    except OSError as e:
        error(f"  Failed to create {target}: {e}")
        return False


def _check_env_key(key: str) -> bool:
    """Check if an environment variable is set and non-empty."""
    value = os.getenv(key, "").strip()
    return len(value) > 0


def check_config_files() -> Tuple[List[str], List[str]]:
    """
    Check which configuration files exist and which are missing.

    Returns:
        Tuple of (present files, missing files)
    """
    present = []
    missing = []

    for target, _source, _description in CONFIG_FILES:
        if _file_exists(target):
            present.append(target)
        else:
            missing.append(target)

    return present, missing


def check_api_keys() -> Tuple[List[str], List[str], List[str]]:
    """
    Check which API keys are configured.

    Returns:
        Tuple of (configured required keys, missing required keys, missing optional keys)
    """
    configured = []
    missing_required = []
    missing_optional = []

    for key, _name, _url in REQUIRED_API_KEYS:
        if _check_env_key(key):
            configured.append(key)
        else:
            missing_required.append(key)

    for key, _name, _url in OPTIONAL_API_KEYS:
        if not _check_env_key(key):
            missing_optional.append(key)

    return configured, missing_required, missing_optional


def run_setup_wizard() -> bool:
    """
    Run the interactive first-time setup wizard.

    Checks for missing config files, offers to create them from examples,
    and validates that critical API keys are configured.

    Returns:
        True if setup is complete enough to proceed
    """
    print()
    info("========== FIRST-TIME SETUP ==========", False)
    print(
        colored(
            "  Welcome! Let's make sure everything is configured correctly.\n",
            "yellow",
        )
    )

    setup_ok = True

    # Step 1: Check config files
    info("Step 1: Checking configuration files...", False)
    _present, missing = check_config_files()

    if not missing:
        success("  All configuration files found.")
    else:
        for target, source, description in CONFIG_FILES:
            if target in missing:
                warning(f"  Missing: {target} ({description})")

                if _file_exists(source):
                    response = question(f"  Create {target} from {source}? (Yes/No): ")
                    if response.strip().lower() in ("yes", "y"):
                        _copy_example_file(target, source)
                        if target == ".env":
                            # Reload dotenv after creating .env
                            try:
                                from dotenv import load_dotenv

                                load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)
                            except ImportError:
                                pass
                    else:
                        warning(f"  Skipped. You'll need to create {target} manually.")
                        if target == ".env":
                            setup_ok = False
                else:
                    error(f"  Example file {source} not found. Please create {target} manually.")
                    if target == ".env":
                        setup_ok = False

    print()

    # Step 2: Check API keys
    info("Step 2: Checking API key configuration...", False)
    configured, missing_required, missing_optional = check_api_keys()

    if configured:
        for key in configured:
            success(f"  {key} is configured")

    if missing_required:
        for key, name, url in REQUIRED_API_KEYS:
            if key in missing_required:
                error(f"  {key} is not set (required for {name})")
                print(colored(f"    Get your key at: {url}", "cyan"))
                print(colored(f"    Then add it to your .env file: {key}=your_key_here", "cyan"))
        setup_ok = False

    if missing_optional:
        for key, name, url in OPTIONAL_API_KEYS:
            if key in missing_optional:
                warning(f"  {key} is not set (optional, needed for {name})")
                print(colored(f"    Get your key at: {url}", "cyan"))

    print()

    # Step 3: Summary
    info("========== SETUP SUMMARY ==========", False)

    if setup_ok:
        success("  Core configuration looks good! You're ready to start.")
        if missing_optional:
            print(
                colored(
                    "  Some optional API keys are missing. You can add them later in .env",
                    "yellow",
                )
            )
    else:
        error("  Some required configuration is missing.")
        print(
            colored(
                "\n  To complete setup:\n"
                "  1. Edit .env with your API keys (see .env.example for reference)\n"
                "  2. Edit config.json for your preferences (see config.example.json)\n"
                "  3. Run the application again\n",
                "yellow",
            )
        )
        print(
            colored(
                "  For detailed setup instructions, see: ENV_SETUP.md\n",
                "cyan",
            )
        )

    info("====================================\n", False)

    return setup_ok


def run_startup_checks() -> bool:
    """
    Run lightweight startup checks (non-interactive).

    Used on subsequent runs (not first time) to warn about missing config
    without blocking the user.

    Returns:
        True if critical configuration is present
    """
    issues = []

    # Check .env exists
    if not _file_exists(".env"):
        issues.append("No .env file found. Copy .env.example to .env and add your API keys.")

    # Check config.json exists
    if not _file_exists("config.json"):
        issues.append("No config.json found. Copy config.example.json to config.json.")

    # Check critical API key
    if not _check_env_key("MISTRAL_API_KEY"):
        issues.append("MISTRAL_API_KEY not set. Text generation features will not work.")

    if issues:
        warning("Configuration warnings:")
        for issue in issues:
            warning(f"  - {issue}")
        print()
        return False

    return True
