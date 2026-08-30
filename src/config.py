# src/config.py

"""
Responsible for setup and retrieval of Anytype API key with the OS keyring
"""

import keyring
import getpass
import os
from pathlib import Path
import yaml

SERVICE_NAME = "anykeep"
USERNAME = "anytype_local_api_key"

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

def set_api_key():
    """Prompts securely for the Anytype API key and saves it to the OS keyring."""
    api_key = getpass.getpass("Enter your Anytype Local API Key: ")
    
    if not api_key: # if no given key
        raise ValueError("API key cannot be empty...")

    # if key is given (no validity check)
    keyring.set_password(SERVICE_NAME, USERNAME, api_key)
    print("API key successfully saved to OS keyring")

def get_api_key():
    """Retrieves the Anytype API key from the OS keyring"""
    api_key = keyring.get_password(SERVICE_NAME, USERNAME)

    # if there is no key found
    if not api_key:
        raise RuntimeError("No API key found in the OS keyring. Run 'anykeep auth --set-key' first")

    # if key was found
    return api_key

def get_config_path() -> Path:
    """Returns to the users config file, creating directories if need be"""
    config_dir = Path.home() / "config" / "anykeep"
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
    
