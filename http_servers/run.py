"""
This module provides functionality to run an Apache HTTP server container using Podman.

The `do_run` function sets up and runs an Apache HTTP server container with specified configurations.
It binds various directories and configuration files from the host to the container to configure the server.

The following directories and files are bound to the container:
- Webroot directory: Mounted to /usr/local/apache2/htdocs (read-only)
- CGI directory: Mounted to /usr/local/apache2/cgi-bin (read-only)
- Let's Encrypt directory: Mounted to /usr/local/apache2/conf/letsencrypt (read-write)
- Apache configuration file: Mounted to /usr/local/apache2/conf/httpd.conf (read-only)
- SSL configuration file: Mounted to /usr/local/apache2/conf/extra/httpd-ssl.conf (read-only)

The container is run with the following settings:
- Image: my-httpd
- Name: apache
- Ports: 80/tcp and 443/tcp are mapped to the host

The container is started in detached mode.
"""
import os
import click
from podman import PodmanClient


def do_run():
    """
    Runs an Apache HTTP server container using Podman with specified configurations.

    This function sets up and runs an Apache HTTP server container using the Podman
    client. It binds various directories and configuration files from the host to the
    container to configure the server.

    The following directories and files are bound to the container:
    - Webroot directory: Mounted to /usr/local/apache2/htdocs (read-only)
    - CGI directory: Mounted to /usr/local/apache2/cgi-bin (read-only)
    - Let's Encrypt directory: Mounted to /usr/local/apache2/conf/letsencrypt (read-write)
    - Apache configuration file: Mounted to /usr/local/apache2/conf/httpd.conf (read-only)
    - SSL configuration file: Mounted to /usr/local/apache2/conf/extra/httpd-ssl.conf (read-only)

    The container is run with the following settings:
    - Image: my-httpd
    - Name: apache
    - Ports: 80/tcp and 443/tcp are mapped to the host

    The container is started in detached mode.
    """
    with PodmanClient() as client:
        webroot_dir = os.path.join(os.path.dirname(__file__), "..", "build", "webroot")
        abs_webroot_dir = os.path.abspath(webroot_dir)
        cgi_dir = os.path.join(os.path.dirname(__file__), "..", "cgi_bin")
        abs_cgi_dir = os.path.abspath(cgi_dir)
        config_file = os.path.join(
            os.path.dirname(__file__), "..", "build", "apache", "conf", "httpd.conf"
        )
        abs_config_file = os.path.abspath(config_file)
        ssl_config_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "build",
            "apache",
            "conf",
            "extra",
            "httpd-ssl.conf",
        )
        abs_ssl_config_file = os.path.abspath(ssl_config_file)
        letsencrypt_dir = os.path.join(
            os.path.dirname(__file__), "..", "build", "certbot", "conf"
        )
        abs_letsencrypt_dir = os.path.abspath(letsencrypt_dir)

        client.containers.run(
            image="my-httpd",
            name="apache",
            ports={"80/tcp": 80, "443/tcp": 443},
            mounts=[
                {
                    "source": abs_webroot_dir,
                    "target": "/usr/local/apache2/htdocs",
                    "type": "bind",
                    "read_only": True,
                },
                {
                    "source": abs_cgi_dir,
                    "target": "/usr/local/apache2/cgi-bin",
                    "type": "bind",
                    "read_only": True,
                },
                {
                    "source": abs_letsencrypt_dir,
                    "target": "/usr/local/apache2/conf/letsencrypt",
                    "type": "bind",
                    "read_only": False,
                },
                {
                    "source": abs_config_file,
                    "target": "/usr/local/apache2/conf/httpd.conf",
                    "type": "bind",
                    "read_only": True,
                },
                {
                    "source": abs_ssl_config_file,
                    "target": "/usr/local/apache2/conf/extra/httpd-ssl.conf",
                    "type": "bind",
                    "read_only": True,
                },
            ],
            detach=True,
        )


@click.command()
def run():
    """
    Executes the main running function for the HTTP server.

    This function calls the `do_run` function to start the server.
    """
    do_run()
