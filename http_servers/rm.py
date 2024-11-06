import click
from podman import PodmanClient

def do_rm():
    with PodmanClient() as client:
        client.containers.get('apache').remove(force=True)
        client.images.remove('my-httpd', force=True)

@click.command()
def rm():
    do_rm()
