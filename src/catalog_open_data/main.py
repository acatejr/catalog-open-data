try:
    from rich import print as rprint
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is absent
    def rprint(*args, **kwargs):
        print(*args, **kwargs)
import click
import os
import json
from pydantic import ValidationError
from catalog_open_data.schema import MapServer

DATA_DIR = "./data"


@click.group()
def cli():
    """Catalog Open Data CLI."""

    if not os.path.exists(DATA_DIR):
        rprint(
            f"[yellow]Data directory '{DATA_DIR}' does not exist. Creating it...[/yellow]"
        )
        os.makedirs(DATA_DIR)


@cli.command()
def health_check():
    """Check the health of the Catalog Open Data application."""
    rprint("[bold blue]Health check passed![/bold blue]")


@cli.command()
@click.argument("name")
def greet(name):
    """Greet a user by name."""
    rprint(f"[green]Hello, {name}![/green]")


@cli.command()
def list_data():
    """List files in the data directory."""
    if not os.path.exists(DATA_DIR):
        rprint(f"[red]Data directory '{DATA_DIR}' does not exist.[/red]")
        return

    files = os.listdir(DATA_DIR)
    if not files:
        rprint("[yellow]No files found in the data directory.[/yellow]")
    else:
        rprint("[bold blue]Files in the data directory:[/bold blue]")
        for file in files:
            rprint(f" - {file}")


@cli.command()
def crawl_data():
    """Crawl data files in the data directory."""

    json_files = []
    # Crawl over the JSON files in the data directory
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".json"):
                if file not in ["opencode.json", "catalog.json", "_index.json"]:
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        json_obj = json.load(f)
                        mapserver = create_mapserver_from_json(json_obj)
                        rprint(
                            f"[green]Validated MapServer JSON file:[/green] {mapserver.documentInfo}"
                        )

                    # json_files.append(file_path)
                    # rprint(f"[green]Found JSON file:[/green] {file}")

    rprint(
        f"[bold blue]Found {len(json_files)} JSON files in the data directory.[/bold blue]"
    )


def create_mapserver_from_json(json_data: dict) -> MapServer:
    """
    Parses and validates a JSON dict into a MapServer Pydantic model.
    Args:
        json_data (dict): The JSON data as a dictionary.
    Returns:
        MapServer: The populated MapServer instance.
    Raises:
        ValidationError: If the JSON data does not match the MapServer schema.
    """
    try:
        return MapServer.model_validate(json_data)
    except ValidationError as e:
        raise ValueError(f"Invalid JSON data for MapServer: {e}")


def main():
    cli()


if __name__ == "__main__":
    crawl_data()
    # main()
