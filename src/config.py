# src/config.py

"""
Responsible for setup and retrieval of Anytype API key with the OS keyring
"""

import keyring
import getpass
import os
from pathlib import Path
import yaml

# The OS keyring is the secure storage layer for the Anytype Local API key.
# All secrets are stored under a single app/service namespace and username.
SERVICE_NAME = "anykeep"
USERNAME = "anytype_local_api_key"

# Default application configuration used when no user config file exists yet.
# This keeps the CLI usable before a real config is created on disk.
DEFAULT_CONFIG = {
    "anytype": {
        "host": "127.0.0.1",
        "port": 3100,
        "target_space_id": "SPACE_ID"
    },
    "ingestion": {
        "watch_directory": "~/Downloads",
        "auto_delete_zip": True
    },
    "storage": {
        "db_path": "~/.config/anykeep/state.db",
        "log_level": "INFO"
    }
}

# The keyring backend is resolved first so we fail early when the host OS has no
# compatible secure storage provider available (e.g. missing SecretService/Keychain).
def get_keyring_backend_name() -> str:
    """Return the active OS keyring backend name for diagnostics and guard rails."""
    try:
        backend = keyring.get_keyring()
        return type(backend).__name__
    except Exception as exc:
        raise RuntimeError(f"No usable OS keyring backend is available: {exc}") from exc


# set_api_key() is the write path: user input is validated, then persisted to the
# platform secure store keyed by the app/service name and username.
def set_api_key(api_key: str = None):
    """Securely stores the Anytype Local API key in the OS keyring."""
    if not api_key:
        api_key = getpass.getpass("Enter your Anytype Local API Key: ")

    if not api_key:
        raise ValueError("API key cannot be empty...")

    try:
        get_keyring_backend_name()
        keyring.set_password(SERVICE_NAME, USERNAME, api_key)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed to access OS keyring backend: {exc}") from exc


# get_api_key() is the read path used by the app when it needs the Anytype Local API
# key for network calls. It verifies the backend exists and raises friendly errors if
# the key has not been stored yet or the system keyring is unavailable.
def get_api_key() -> str:
    """Retrieves the Anytype API key from the OS keyring with robust error handling."""
    try:
        get_keyring_backend_name()
        api_key = keyring.get_password(SERVICE_NAME, USERNAME)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed to retrieve API key from OS keyring: {exc}") from exc

    if not api_key:
        raise RuntimeError("No API key found in the OS keyring. Run 'anykeep auth --set-key' first")

    return api_key

def get_config_path() -> Path:
    """Returns to the users config file, creating directories if need be"""
    config_dir = Path.home() / ".config" / "anykeep"
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir / "config.yaml"

def load_config() -> dict:
    """Loads the YAML config file, falling back to defaults if missing."""
    config_path  = get_config_path()

    # check if it does not exist
    if not config_path.exists():
        return DEFAULT_CONFIG

    # if it does, attempt opening the file
    try:
        with open(config_path, "r") as file:
            user_config = yaml.safe_load(file) or {}
            config = DEFAULT_CONFIG.copy()

            # attempting to load config values
            for section, values in user_config.items():
                if section in config and isinstance(values, dict):
                    config[section].update(values)

            # if config loading was successful
            return config
    except Exception as e:
        raise RuntimeError(f"Failed to load config file at {config_path}: {e}")
    
