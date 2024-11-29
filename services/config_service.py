"""
A module that allows users to read and update configuration settings.
"""

from typing import Any, Dict, Optional, TypeVar
import copy
import json
import yaml
import logging
from pydantic import BaseModel


from configuration.app import Config

T = TypeVar("T")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_yaml_config(file_path: str) -> Optional[dict]:
    """Load a YAML file"""
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)
    return None


def parse_yaml_config(file_path: str) -> Config:
    """Load configuration from a YAML file"""
    with open(file_path, "r", encoding="utf-8") as file:
        config_data = yaml.safe_load(file)
    return Config(**config_data)


def load_json_config(file_path: str) -> Optional[dict]:
    """Load a JSON file"""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_json_config(json_str: str) -> Config:
    """Update the configuration with JSON input"""
    json_data = json.loads(json_str)
    return Config(**json_data)


def merge_config(existing_config: BaseModel, update_dict: Dict[str, Any]) -> BaseModel:
    """
    Merge a configuration object with a dictionary update

    Args:
        existing_config: Original configuration object
        update_dict: Dictionary containing updates

    Returns:
        Updated configuration object
    """
    for key, value in update_dict.items():
        if isinstance(value, dict):
            nested_config = getattr(existing_config, key)
            updated_nested_config = merge_config(nested_config, value)
            setattr(existing_config, key, updated_nested_config)
        else:
            # Check if the attribute exists before setting it
            if hasattr(existing_config, key):
                setattr(existing_config, key, value)
            else:
                # Let's log a warning if the attribute does not exist
                logger.warning(f"Attribute {key} does not exist in the configuration")

    return existing_config


def copy_merge_config(config: T, update_dict: Dict[str, Any]) -> T:
    """
    Merge a configuration object with a dictionary update

    Args:
        config: Original configuration object
        update_dict: Dictionary containing updates

    Returns:
        Updated configuration object
    """
    # Create a deep copy to avoid modifying the original
    merged_config = copy.deepcopy(config)

    for key, value in update_dict.items():
        # Handle nested dictionaries recursively
        if hasattr(merged_config, key):
            current_value = getattr(merged_config, key)

            # Recursive merge for nested objects
            if isinstance(value, dict) and hasattr(current_value, "__dict__"):
                nested_config = merge_config(current_value, value)
                setattr(merged_config, key, nested_config)
            else:
                # Direct attribute update
                setattr(merged_config, key, value)

    return merged_config


class ConfigService:
    """
    A service to provide configuration settings and configuration update
    functionality.
    """

    def __init__(self, config: Config):
        self.config = config

    def load_yaml_config(self, file_path: str) -> Optional[dict]:
        """
        Load a configuration file. Merges changes with Config by overwriting
        existing values and loading the yaml Config values in their place.

        Args:
            file_path: The path to the configuration file.

        Returns:
            The loaded configuration dictionary.
        """
        yaml_config = load_yaml_config(file_path)
        merge_config(self.config, yaml_config)
        return yaml_config

    def load_json_config(self, json_str: str) -> Optional[dict]:
        """
        Load a JSON string. Merges changes with Config by overwriting
        existing values and loading the JSON Config values in their place.

        Args:
            json_str: The JSON string to load.

        Returns:
            The loaded configuration dictionary.
        """
        json_config = load_json_config(json_str)
        merge_config(self.config, json_config)
        return json_config
