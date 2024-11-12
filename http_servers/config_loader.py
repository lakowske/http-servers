import yaml
import os
from pathlib import Path
import argparse


class ConfigurationLoader:

    @staticmethod
    def load_yaml(config_path: str) -> dict:
        if not config_path or not Path(config_path).exists():
            return {}
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def load_env() -> dict:
        return {
            "podman": {
                "socket_url": os.getenv("PODMAN_SOCKET_URL"),
                "timeout": os.getenv("PODMAN_TIMEOUT"),
                "tls_verify": os.getenv("PODMAN_TLS_VERIFY", "1").lower()
                in ("true", "1", "yes"),
                "cert_path": os.getenv("PODMAN_CERT_PATH"),
            }
        }

    @staticmethod
    def load_cli() -> dict:
        parser = argparse.ArgumentParser()
        parser.add_argument("--podman-socket", help="Podman socket URL")
        parser.add_argument("--podman-timeout", type=int, help="Podman API timeout")
        parser.add_argument(
            "--podman-tls-verify", type=bool, help="Podman TLS verification"
        )
        parser.add_argument("--podman-cert-path", help="Podman certificate path")

        args, _ = parser.parse_known_args()

        config = {"podman": {}}
        if args.podman_socket:
            config["podman"]["socket_url"] = args.podman_socket
        if args.podman_timeout:
            config["podman"]["timeout"] = args.podman_timeout
        if args.podman_tls_verify is not None:
            config["podman"]["tls_verify"] = args.podman_tls_verify
        if args.podman_cert_path:
            config["podman"]["cert_path"] = args.podman_cert_path

        return config

    @staticmethod
    def merge_configs(*configs: dict) -> dict:
        final_config = {}
        for config in configs:
            for section, values in config.items():
                if section not in final_config:
                    final_config[section] = {}
                for key, value in (values or {}).items():
                    if value is not None:
                        final_config[section][key] = value
        return final_config


@staticmethod
def load_configs(config_path: str = None) -> dict:
    loader = ConfigurationLoader()
    yaml_config = loader.load_yaml(config_path)
    env_config = loader.load_env()
    cli_config = loader.load_cli()
    return loader.merge_configs(yaml_config, env_config, cli_config)
