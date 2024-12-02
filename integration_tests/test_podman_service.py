import os
from configuration.container import ServerContainer
from configuration.app import WORKSPACE


container = ServerContainer()
podman_service = container.podman_service()
config_service = container.config_service()


def test_podman_list_containers():
    """
    Test that the podman service can list containers.
    """

    containers = podman_service.list_containers()
    assert containers is not None
    assert len(containers) >= 0


def test_podman_build_image():
    """
    Test that the podman service can build an image.
    """
    apache_path = config_service.config.build_paths.get("apache").tree_root_path(
        WORKSPACE
    )
    apache_dockerfile = f"{apache_path}/Dockerfile"

    if not os.path.exists(apache_path):
        raise FileNotFoundError(f"Could not find {apache_dockerfile}")

    image_id, build_output = podman_service.build_image(
        path=apache_path, dockerfile=apache_dockerfile, tag="httpd-nexus:latest"
    )
    assert image_id is not None
    for line in build_output:
        print(line)


def test_podman_run_container():
    """
    Test that the podman service can run a container.
    """
    webroot_path = config_service.config.build_paths.get("webroot").tree_root_path(
        WORKSPACE
    )
    cgi_path = config_service.config.build_paths.get("cgi").tree_root_path(WORKSPACE)
    httpd_config_path = (
        config_service.config.build_paths.get("apache")
        .get("conf")
        .get("httpd.conf")
        .tree_root_path(WORKSPACE)
    )
    ssl_config_path = (
        config_service.config.build_paths.get("apache")
        .get("conf")
        .get("extra")
        .get("httpd-ssl.conf")
        .tree_root_path(WORKSPACE)
    )
    letsencrypt_path = config_service.config.build_paths.get(
        "letsencrypt"
    ).tree_root_path(WORKSPACE)

    container_id = podman_service.run_container(
        image="httpd-nexus:latest",
        name="httpd-nexus",
        ports={"80/tcp": 80, "443/tcp": 443},
        mounts=[
            {
                "target": "/usr/local/apache2/htdocs",
                "source": webroot_path,
                "type": "bind",
                "read_only": False,
            },
            {
                "target": "/usr/local/apache2/cgi-bin",
                "source": cgi_path,
                "type": "bind",
                "read_only": False,
            },
            {
                "target": "/usr/local/apache2/letsencrypt",
                "source": letsencrypt_path,
                "type": "bind",
                "read_only": False,
            },
            {
                "target": "/usr/local/apache2/conf/httpd.conf",
                "source": httpd_config_path,
                "type": "bind",
                "read_only": False,
            },
            {
                "target": "/usr/local/apache2/conf/extra/httpd-ssl.conf",
                "source": ssl_config_path,
                "type": "bind",
                "read_only": False,
            },
        ],
        environment={},
    )

    assert container_id is not None
