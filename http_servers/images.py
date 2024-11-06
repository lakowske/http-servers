import click
import os
from podman import PodmanClient
from .config import load_config, apache_dir, certbot_dir

def build_images():
    config = load_config()
    apache_path = os.path.abspath(apache_dir(config))
    apache_dockerfile = os.path.join(apache_path, 'Dockerfile')

    if not os.path.exists(apache_path):
        raise click.ClickException(f"Apache directory not found: {apache_path}")

    with PodmanClient() as client:
        try:
            apacheid, apache_report = client.images.build(path=apache_path, dockerfile=apache_dockerfile, tag='my-httpd')
            for line in apache_report:
                print(line)
        except Exception as e:
            raise e


@click.command()
def images():
    build_images()