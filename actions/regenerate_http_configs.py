#!/usr/local/venv/bin/python
"""
Script to regenerate HTTP configs from unified users JSON file.
Runs inside the HTTP container.
"""

import json
import logging
import os
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_unified_users(json_path: str) -> list:
    """Load unified users from JSON file."""
    try:
        if not os.path.exists(json_path):
            logger.warning("Users file %s does not exist", json_path)
            return []

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("users", [])
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", json_path, e)
        return []
    except Exception as e:
        logger.error("Error loading users from %s: %s", json_path, e)
        return []


def generate_htpasswd_file(users: list, file_path: str):
    """Generate Apache htpasswd file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Clear existing file
        with open(file_path, "w", encoding="utf-8"):
            pass

        # Add each user with HTTP access
        for user in users:
            if "http" in user.get("enabled_services", []):
                try:
                    subprocess.run(
                        ["htpasswd", "-b", file_path, user["username"], user["password"]],
                        check=True,
                        capture_output=True,
                    )
                    logger.info("Added user %s to htpasswd", user["username"])
                except subprocess.CalledProcessError as e:
                    logger.error("Failed to add user %s to htpasswd: %s", user["username"], e)

        # Set proper ownership and permissions
        subprocess.run(["chown", "www-data:www-data", file_path], check=True)
        subprocess.run(["chmod", "640", file_path], check=True)

        logger.info("Generated htpasswd file: %s", file_path)

    except Exception as e:
        logger.error("Error generating htpasswd file: %s", e)


def generate_passwd_file(users: list, file_path: str):
    """Generate plain text passwd file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            for user in users:
                if "http" in user.get("enabled_services", []):
                    f.write(f"{user['username']}:{user['password']}\n")

        # Set proper ownership and permissions
        subprocess.run(["chown", "www-data:www-data", file_path], check=True)
        subprocess.run(["chmod", "640", file_path], check=True)

        logger.info("Generated passwd file: %s", file_path)

    except Exception as e:
        logger.error("Error generating passwd file: %s", e)


def reload_apache():
    """Reload Apache configuration."""
    try:
        subprocess.run(["apache2ctl", "graceful"], check=True, capture_output=True)
        logger.info("Apache reloaded successfully")
    except subprocess.CalledProcessError as e:
        logger.error("Failed to reload Apache: %s", e)
    except FileNotFoundError:
        logger.warning("apache2ctl not found, skipping Apache reload")


def regenerate_http_configs(users_json_path: str = "/secrets/unified_users.json"):
    """Main function to regenerate all HTTP configs."""
    logger.info("Starting HTTP config regeneration")

    # Load users
    users = load_unified_users(users_json_path)
    http_users = [u for u in users if "http" in u.get("enabled_services", [])]
    logger.info("Found %d users with HTTP access", len(http_users))

    # Generate config files
    htpasswd_path = "/usr/local/apache2/conf/git-auth"
    passwd_path = "/usr/local/apache2/conf/passwd"

    generate_htpasswd_file(users, htpasswd_path)
    generate_passwd_file(users, passwd_path)

    # Reload Apache
    reload_apache()

    logger.info("HTTP config regeneration completed")


if __name__ == "__main__":
    users_json = sys.argv[1] if len(sys.argv) > 1 else "/secrets/unified_users.json"
    regenerate_http_configs(users_json)
