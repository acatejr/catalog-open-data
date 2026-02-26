"""
Command-line interface for the MapServer catalog search.
"""

import argparse
import json
import sys
from pathlib import Path

from dbsearch.schema import init_database, clear_database
from dbsearch.indexer import MapServerIndexer
from dbsearch.search import MapServiceCatalog


def cmd_index(args):
    """Index MapServer JSON files into the database."""
    print(f"Initializing database: {args.db}")
    conn = init_database(args.db)

    if args.clear:
        print("Clearing existing data...")
        clear_database(conn)

    indexer = MapServerIndexer(conn)
    stats = indexer.index_directory(args.data_dir, verbose=not args.quiet)

    conn.close()
    return 0 if stats['failed'] == 0 else 1


def cmd_search(args):
    """Search for map services."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)

    results = catalog.search(args.query, limit=args.limit)

    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        print(f"\nFound {len(results)} results:\n")
        for i, service in enumerate(results, 1):
            print(f"{i}. {service['title'] or service['map_name']}")
            print(f"   Map Name: {service['map_name']}")
            if service['folder_path']:
                print(f"   Folder: {service['folder_path']}")
            if service['keywords']:
                print(f"   Keywords: {service['keywords']}")
            print()

    conn.close()
    return 0


def cmd_keyword(args):
    """Search by keyword."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)

    results = catalog.search_by_keyword(args.keyword, exact=args.exact, limit=args.limit)

    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        print(f"\nFound {len(results)} services with keyword '{args.keyword}':\n")
        for i, service in enumerate(results, 1):
            print(f"{i}. {service['title'] or service['map_name']}")
            print(f"   Map Name: {service['map_name']}")
            print(f"   Folder: {service['folder_path']}")
            print()

    conn.close()
    return 0


def cmd_folder(args):
    """List services in a folder."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)

    results = catalog.find_by_folder(args.folder, limit=args.limit)

    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        print(f"\nFound {len(results)} services in folder '{args.folder}':\n")
        for i, service in enumerate(results, 1):
            print(f"{i}. {service['title'] or service['map_name']}")
            print(f"   Map Name: {service['map_name']}")
            if service['service_description']:
                desc = service['service_description'][:100]
                print(f"   Description: {desc}{'...' if len(service['service_description']) > 100 else ''}")
            print()

    conn.close()
    return 0


def cmd_info(args):
    """Get detailed information about a service."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)

    service = catalog.get_service_by_name(args.service_name)

    if not service:
        print(f"Service '{args.service_name}' not found")
        conn.close()
        return 1

    if args.format == 'json':
        # Include layers and keywords
        service['layers'] = catalog.get_service_layers(service['id'])
        service['keywords_list'] = catalog.get_service_keywords(service['id'])
        print(json.dumps(service, indent=2))
    else:
        print(f"\n{'='*70}")
        print(f"Service: {service['title'] or service['map_name']}")
        print(f"{'='*70}")
        print(f"Map Name: {service['map_name']}")
        print(f"Folder: {service['folder_path']}")
        print(f"Version: {service['version']}")
        print(f"Capabilities: {service['capabilities']}")
        print(f"\nDescription:")
        print(f"  {service['service_description']}")
        print(f"\nKeywords:")
        keywords = catalog.get_service_keywords(service['id'])
        print(f"  {', '.join(keywords)}")
        print(f"\nSpatial Reference: WKID {service['spatial_reference_wkid']}")
        print(f"Extent: ({service['extent_xmin']}, {service['extent_ymin']}) to ({service['extent_xmax']}, {service['extent_ymax']})")
        print(f"Scale: {service['min_scale']} - {service['max_scale']}")

        layers = catalog.get_service_layers(service['id'])
        if layers:
            print(f"\nLayers ({len(layers)}):")
            for layer in layers:
                print(f"  {layer['layer_id']}: {layer['layer_name']}")
                print(f"     Type: {layer['layer_type']}, Geometry: {layer['geometry_type']}")

        print(f"\nFile: {service['file_path']}")
        print()

    conn.close()
    return 0


def cmd_list_folders(args):
    """List all folders."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)

    folders = catalog.list_all_folders()

    if args.format == 'json':
        print(json.dumps(folders, indent=2))
    else:
        print(f"\nFolders ({len(folders)}):\n")
        for folder in folders:
            print(f"  - {folder}")
        print()

    conn.close()
    return 0


def cmd_list_keywords(args):
    """List all keywords with counts."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)

    keywords = catalog.list_all_keywords()

    if args.format == 'json':
        print(json.dumps([{'keyword': k, 'count': c} for k, c in keywords], indent=2))
    else:
        print(f"\nKeywords ({len(keywords)}):\n")
        for keyword, count in keywords[:args.limit]:
            print(f"  {keyword}: {count}")
        print()

    conn.close()
    return 0


def cmd_stats(args):
    """Show catalog statistics."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)

    stats = catalog.get_stats()

    if args.format == 'json':
        print(json.dumps(stats, indent=2))
    else:
        print("\nCatalog Statistics:")
        print(f"  Total Services: {stats['total_services']}")
        print(f"  Total Layers: {stats['total_layers']}")
        print(f"  Unique Keywords: {stats['unique_keywords']}")
        print(f"  Folders: {stats['folders']}")
        print()

    conn.close()
    return 0


def cmd_geometry(args):
    """Search by geometry type."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)

    results = catalog.find_by_geometry_type(args.geometry_type, limit=args.limit)

    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        print(f"\nFound {len(results)} services with geometry type '{args.geometry_type}':\n")
        for i, service in enumerate(results, 1):
            print(f"{i}. {service['title'] or service['map_name']}")
            print(f"   Map Name: {service['map_name']}")
            print(f"   Folder: {service['folder_path']}")
            print()

    conn.close()
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='MapServer Catalog Search - Query USDA Forest Service MapServer metadata'
    )
    parser.add_argument(
        '--db',
        default='mapserver_catalog.db',
        help='Path to the SQLite database (default: mapserver_catalog.db)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Index command
    parser_index = subparsers.add_parser('index', help='Index MapServer JSON files')
    parser_index.add_argument(
        'data_dir',
        help='Directory containing MapServer JSON files'
    )
    parser_index.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing data before indexing'
    )
    parser_index.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    parser_index.set_defaults(func=cmd_index)

    # Search command
    parser_search = subparsers.add_parser('search', help='Full-text search')
    parser_search.add_argument('query', help='Search query')
    parser_search.add_argument('--limit', type=int, default=100, help='Maximum results')
    parser_search.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser_search.set_defaults(func=cmd_search)

    # Keyword command
    parser_keyword = subparsers.add_parser('keyword', help='Search by keyword')
    parser_keyword.add_argument('keyword', help='Keyword to search for')
    parser_keyword.add_argument('--exact', action='store_true', help='Exact match only')
    parser_keyword.add_argument('--limit', type=int, default=100, help='Maximum results')
    parser_keyword.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser_keyword.set_defaults(func=cmd_keyword)

    # Folder command
    parser_folder = subparsers.add_parser('folder', help='List services in a folder')
    parser_folder.add_argument('folder', help='Folder name')
    parser_folder.add_argument('--limit', type=int, default=100, help='Maximum results')
    parser_folder.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser_folder.set_defaults(func=cmd_folder)

    # Info command
    parser_info = subparsers.add_parser('info', help='Get service details')
    parser_info.add_argument('service_name', help='Map service name')
    parser_info.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser_info.set_defaults(func=cmd_info)

    # List folders command
    parser_list_folders = subparsers.add_parser('list-folders', help='List all folders')
    parser_list_folders.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser_list_folders.set_defaults(func=cmd_list_folders)

    # List keywords command
    parser_list_keywords = subparsers.add_parser('list-keywords', help='List all keywords')
    parser_list_keywords.add_argument('--limit', type=int, default=50, help='Maximum keywords to show')
    parser_list_keywords.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser_list_keywords.set_defaults(func=cmd_list_keywords)

    # Stats command
    parser_stats = subparsers.add_parser('stats', help='Show catalog statistics')
    parser_stats.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser_stats.set_defaults(func=cmd_stats)

    # Geometry command
    parser_geometry = subparsers.add_parser('geometry', help='Search by geometry type')
    parser_geometry.add_argument('geometry_type', help='Geometry type (e.g., esriGeometryPolygon)')
    parser_geometry.add_argument('--limit', type=int, default=100, help='Maximum results')
    parser_geometry.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser_geometry.set_defaults(func=cmd_geometry)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
