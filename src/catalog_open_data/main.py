from rich import print as rprint
import requests
import json
from pathlib import Path
from typing import Iterable, Optional

FS_SERVICES_INDEX_URL = "https://apps.fs.usda.gov/arcx/rest/services?f=pjson"
BASE_DATA_DIR = "data"
SERVICE_CATALOG_FILE = f"./{BASE_DATA_DIR}/service_catalog.json"

def create_directories(base_path: str, subdirs: Optional[Iterable[str]] = None) -> None:
    """
    Ensure a base directory exists and optionally create multiple subdirectories under it.

    Args:
        base_path: The root directory to create.
        subdirs: An optional iterable of subdirectory paths (relative to base_path) to create.
    """
    try:
        base = Path(base_path)
        base.mkdir(parents=True, exist_ok=True)

        if subdirs:
            for sd in subdirs:
                sub_path = base.joinpath(sd)
                sub_path.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        rprint(f"[red]Failed to create directories for {base_path}:[/red] {exc}")


def main() -> None:

    resp = requests.get(FS_SERVICES_INDEX_URL)

    if not resp.ok:
        rprint(f"[red]Failed to fetch data from {FS_SERVICES_INDEX_URL}[/red]")
        return

    data = resp.json()
    folders = data.get("folders", [])

    if not folders:
        rprint("[yellow]No service folders found in the response.[/yellow]")
        return
    else:
        service_folders = {}

        for folder in folders:
            # create_directories(BASE_DATA_DIR, subdirs=[folder])

            service_folder_url = (
                f"https://apps.fs.usda.gov/arcx/rest/services/{folder}?f=pjson"
            )
            service_folder_resp = requests.get(service_folder_url)
            service_folders[folder] = service_folder_resp.json()

            folder_services = service_folders[folder].get("services", [])
            for idx, folder_service in enumerate(folder_services):
                service_name = folder_service.get("name", "unknown_service")
                # create_directories(BASE_DATA_DIR, subdirs=[service_name])
                service_type = folder_service.get("type", "unknown_type")
                service_mapserver_url = f"https://apps.fs.usda.gov/arcx/rest/services/{service_name}/{service_type}?f=pjson"
                rprint(f"[blue]Fetching details for service:[/blue] {service_mapserver_url}")
                service_mapserver_resp = requests.get(service_mapserver_url)
                service_folders[folder]["services"][idx]["mapserver_details"] = (
                    service_mapserver_resp.json()
                )

            with open(SERVICE_CATALOG_FILE, "w", encoding="utf-8") as f:
                json.dump(service_folders, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

# rprint(f"[green]Wrote service folders to {SERVICE_CATALOG_FILE}[/green]")

