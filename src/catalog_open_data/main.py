from rich import print as rprint
import requests
import json

FS_SERVICES_INDEX_URL = "https://apps.fs.usda.gov/arcx/rest/services?f=pjson"
SERVICE_CATALOG_FILE = "service_catalog.json"


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
            service_folder_url = (
                f"https://apps.fs.usda.gov/arcx/rest/services/{folder}?f=pjson"
            )
            service_folder_resp = requests.get(service_folder_url)
            service_folders[folder] = service_folder_resp.json()

            folder_services = service_folders[folder].get("services", [])
            for idx, folder_service in enumerate(folder_services):
                service_name = folder_service.get("name", "unknown_service")
                service_type = folder_service.get("type", "unknown_type")
                service_mapserver_url = f"https://apps.fs.usda.gov/arcx/rest/services/{service_name}/{service_type}?f=pjson"
                service_mapserver_resp = requests.get(service_mapserver_url)
                service_folders[folder]["services"][idx]["mapserver_details"] = (
                    service_mapserver_resp.json()
                )

        with open(SERVICE_CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump(service_folders, f, ensure_ascii=False, indent=2)

        rprint(f"[green]Wrote service folders to {SERVICE_CATALOG_FILE}[/green]")


if __name__ == "__main__":
    main()


# except requests.RequestException as e:
#     rprint(f"[red]Request error for {service_url}:[/red] {e}")
#     continue

# https://apps.fs.usda.gov/arcx/rest/services/RDW_LandscapeAndWildlife/2010_Land_Cover_Of_North_America_CEC_250m/MapServer?f=pjson

# rprint(f"[green]Compiled service catalog with {len(service_catalog)} entries.[/green]")
# rprint(f"[blue]Successfully fetched folder:[/blue] {service_url}")
# folder_json = service_resp.json()


# Test if the URL is reachable before making the main request
# try:
#     test_resp = requests.head(service_url, timeout=5)
#     if not test_resp.ok:
#         rprint(ffoldersw]HEAD re4uest failed for {service_url}[/yellow]")
#         continue
# except requests.RequestException as e:
#     rprint(f"[red]HEAD request error for {service_url}:[/red] {e}")
#     continue

# try:
#     requests.utils.requote_uri(service_url)  # Validate URL format
# except Exception as e:
#     rprint(f"[red]Invalid URL:[/red] {service_url} - {e}")
#     continue

# try:
#     service_resp = requests.get(service_url, timeout=10)
#     if not service_resp.ok:
#         rprint(f"[yellow]Failed to fetch data from {service_url}[/yellow]")
#         continue
