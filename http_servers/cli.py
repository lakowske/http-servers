import click
from .templates import templates
from .images import images
from .run import run
from .rm import rm

@click.group()
def cli():
    pass

cli.add_command(templates)
cli.add_command(images)
cli.add_command(run)
cli.add_command(rm)

if __name__ == '__main__':
    cli()