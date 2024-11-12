from http_servers.container import Container


def initialize_container(config_path: str = None) -> Container:

    # Create and configure the container
    container = Container()

    # Merge configurations with precedence: CLI > ENV > YAML
    # Load configurations from different sources
    merged_config = container.loaded_configs()

    # Apply the merged configuration to the container
    container.config.from_dict(merged_config)

    # Load the configuration into the container
    # container.load_config()

    # Wire the container to modules that use dependency injection
    container.wire(modules=[__name__])

    return container
