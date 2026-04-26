import click

from {{project_name_snake}} import __version__


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    pass


@main.command()
@click.argument("name", default="World")
def hello(name: str) -> None:
    click.echo(f"Hello, {name}!")
