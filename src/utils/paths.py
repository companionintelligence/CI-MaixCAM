"""
Canonical Filesystem Paths
Single source of truth for on-device configuration file locations

Author: Companion Intelligence
Date: August 26, 2026
"""

import json
import os

# Canonical on-device configuration file.
#
# Every component that reads or writes device configuration must use this
# constant. It is the path the setup screen has always written to and the
# path main.py has always read back, so it is where deployed devices
# actually hold their data.
CONFIG_PATH = "/sd/companion_config.json"

# Paths used by earlier builds. Read-only: kept so a device configured by an
# older build does not silently lose its settings when it is upgraded.
LEGACY_CONFIG_PATHS = (
    "/sd/config/app_config.json",
)


def migrate_legacy_config(config_path=CONFIG_PATH):
    """Seed the canonical config file from a legacy path if it is absent

    Never overwrites an existing canonical file. Returns the legacy path that
    was migrated, or None when there was nothing to do.
    """
    try:
        if os.path.exists(config_path):
            return None

        for legacy_path in LEGACY_CONFIG_PATHS:
            if not os.path.exists(legacy_path):
                continue

            with open(legacy_path, 'r') as legacy_file:
                legacy_config = json.load(legacy_file)

            ensure_config_dir(config_path)

            with open(config_path, 'w') as config_file:
                json.dump(legacy_config, config_file, indent=2)

            print(f"Migrated configuration from {legacy_path} to {config_path}")
            return legacy_path

        return None

    except Exception as e:
        print(f"Error migrating legacy configuration: {e}")
        return None


def ensure_config_dir(config_path=CONFIG_PATH):
    """Create the directory holding the config file if it does not exist

    Returns True when the directory is usable. Off-device (where /sd does not
    exist and cannot be created) this returns False rather than raising, so a
    desktop import of the config module does not blow up.
    """
    config_dir = os.path.dirname(config_path)
    if not config_dir:
        return True

    try:
        os.makedirs(config_dir, exist_ok=True)
        return True
    except OSError as e:
        print(f"Could not create config directory {config_dir}: {e}")
        return False
