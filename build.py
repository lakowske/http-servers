"""
Can do the following actions:
1. Renders the configuration tree into a build directory
2. Builds the image using the build directory
3. Runs the container
4. Does a health check on the container
5. Runs certbot to get a certificates from Let's Encrypt
6. Reloads the configuration

"""

from configuration.tree_walker import TreeRenderer
from configuration.container import ServerContainer
from http_server.health_check import healthcheck


container = ServerContainer()
podman_service = container.podman_service()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
httpd_service = container.httpd_service()


def build():
    walker = TreeRenderer()
    walker.walk(config_service.config.build_paths, config_service.config)
    image_id, build_output = httpd_service.build_image("httpd-nexus:latest")


def run():
    httpd_container = httpd_service.run_container("httpd-nexus:latest", "httpd-nexus")
    assert httpd_container is not None
    assert httpd_service.is_container_running(httpd_container.id)


def health():
    domain = config_service.config.admin.domain
    assert healthcheck(domain)


def certificates():
    certbot = container.certbot_service()
    success = certbot.create_certificate(
        config_service.config.admin.domain, dry_run=False, staging=False
    )
    assert success is True


def reload():
    certbot = container.certbot_service()
    success = certbot.update_apache_configs_to_letsencrypt(
        config_service.config.admin.domain
    )
    assert success
    container_id = httpd_service.get_container_id("httpd-nexus")
    assert container_id is not None
    httpd_service.reload_configuration(container_id)
    assert httpd_service.is_container_running(container_id)
