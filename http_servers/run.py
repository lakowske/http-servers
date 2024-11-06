import os
import click
from podman import PodmanClient
from .config import load_config
from http_servers.config import ssl_config_path


def do_run(domain, email):
    config = load_config()
    with PodmanClient() as client:
        webroot_dir = os.path.join(os.path.dirname(__file__), '..', 'build', 'webroot')
        abs_webroot_dir = os.path.abspath(webroot_dir)
        config_file = os.path.join(os.path.dirname(__file__), '..', 'build', 'apache', 'conf', 'httpd.conf')
        abs_config_file = os.path.abspath(config_file)
        ssl_config_file = os.path.join(os.path.dirname(__file__), '..', 'build', 'apache', 'conf', 'extra', 'httpd-ssl.conf')
        abs_ssl_config_file = os.path.abspath(ssl_config_file)
        letsencrypt_dir = os.path.join(os.path.dirname(__file__), '..', 'build', 'letsencrypt')
        abs_letsencrypt_dir = os.path.abspath(letsencrypt_dir)

        client.containers.run(
            image='my-httpd',
            name='apache',
            ports={'80/tcp': 80, '443/tcp': 443},
            mounts=[{'source': abs_webroot_dir, 'target': '/usr/local/apache2/htdocs', 'type': 'bind', 'read_only': True},
                    {'source': abs_letsencrypt_dir, 'target': '/etc/letsencrypt', 'type': 'bind', 'read_only': False},
                    {'source': abs_config_file, 'target': '/usr/local/apache2/conf/httpd.conf', 'type': 'bind', 'read_only': True},
                    {'source': abs_ssl_config_file, 'target': '/usr/local/apache2/conf/extra/httpd-ssl.conf', 'type': 'bind', 'read_only': True}],
            detach=True
        )

@click.command()
@click.option('--domain', required=True, help='The domain name for the SSL certificate.')
@click.option('--email', required=True, help='The email address for the SSL certificate registration.')
def run(domain, email):
    do_run(domain, email)