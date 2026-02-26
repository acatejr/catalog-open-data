# MapServer Catalog Database Search

A SQLite-based catalog and search system for USDA Forest Service ArcGIS MapServer metadata.

## Overview

This module provides a searchable database catalog for MapServer JSON metadata files. It indexes service information, layers, keywords, and spatial extents to enable fast querying and discovery of map services.

## Features

- **Full-text search** across service names, titles, descriptions, and keywords
- **Keyword-based search** with exact or partial matching
- **Folder browsing** to explore services by directory structure
- **Geometry type filtering** to find services with specific geometry types
- **Spatial extent queries** to find services covering geographic areas
- **Capability filtering** to find services with specific capabilities (Query, Data, Map)
- **CLI interface** with multiple commands
- **JSON and text output** formats

## Installation

No additional dependencies are required beyond Python 3.13+ and the standard library.

## Database Schema

### Tables

1. **mapservices** - Core service metadata
   - Service identification (map_name, title)
   - Descriptions and documentation
   - Spatial reference and extent
   - Scale ranges
   - Capabilities

2. **layers** - Layer information for each service
   - Layer ID and name
   - Geometry and layer types
   - Scale ranges

3. **keywords** - Normalized keyword table
   - Individual keywords linked to services
   - Enables efficient keyword searches

4. **mapservices_fts** - Full-text search index
   - Virtual FTS5 table for fast text search

## Usage

### Command Line Interface

#### 1. Index MapServer JSON Files

Build the catalog database from your JSON files:

```bash
# Index all MapServer JSON files in the data directory
python -m dbsearch.cli index data/

# Clear existing data and re-index
python -m dbsearch.cli index data/ --clear

# Use a custom database file
python -m dbsearch.cli --db custom.db index data/
```

#### 2. Search Commands

**Full-text search:**
```bash
# Search across all text fields
python -m dbsearch.cli search "fire management"

# Limit results
python -m dbsearch.cli search "forest" --limit 10

# JSON output
python -m dbsearch.cli search "wildfire" --format json
```

**Search by keyword:**
```bash
# Partial match (default)
python -m dbsearch.cli keyword "FACTS"

# Exact match only
python -m dbsearch.cli keyword "USDA Forest Service" --exact
```

**Browse by folder:**
```bash
# List all services in the EDW folder
python -m dbsearch.cli folder EDW

# List all available folders
python -m dbsearch.cli list-folders
```

**Get service details:**
```bash
# Get detailed information about a specific service
python -m dbsearch.cli info EDW_ActivityFactsCommonAttributes_01
```

**Search by geometry type:**
```bash
# Find all polygon services
python -m dbsearch.cli geometry esriGeometryPolygon

# Find point services
python -m dbsearch.cli geometry esriGeometryPoint
```

**Browse keywords:**
```bash
# List all keywords with usage counts
python -m dbsearch.cli list-keywords

# Show top 100 keywords
python -m dbsearch.cli list-keywords --limit 100
```

**View statistics:**
```bash
# Show catalog statistics
python -m dbsearch.cli stats
```

### Python API

Use the catalog programmatically in your Python code:

```python
from dbsearch.schema import init_database
from dbsearch.indexer import MapServerIndexer
from dbsearch.search import MapServiceCatalog

# Initialize database
conn = init_database('mapserver_catalog.db')

# Index files (one-time setup)
indexer = MapServerIndexer(conn)
indexer.index_directory('data/')

# Create catalog search interface
catalog = MapServiceCatalog(conn)

# Full-text search
results = catalog.search("fire management")
for service in results:
    print(f"{service['title']}: {service['map_name']}")

# Search by keyword
services = catalog.search_by_keyword("FACTS", exact=True)

# Find services in a folder
edw_services = catalog.find_by_folder("EDW")

# Get service details
service = catalog.get_service_by_name("EDW_ActivityFactsCommonAttributes_01")
layers = catalog.get_service_layers(service['id'])
keywords = catalog.get_service_keywords(service['id'])

# Find by geometry type
polygon_services = catalog.find_by_geometry_type("esriGeometryPolygon")

# Spatial extent search
services_in_area = catalog.find_by_spatial_extent(
    xmin=-120.0, ymin=35.0, xmax=-115.0, ymax=40.0
)

# Get statistics
stats = catalog.get_stats()
print(f"Total services: {stats['total_services']}")

# Close connection
conn.close()
```

## Module Structure

```
dbsearch/
├── __init__.py          # Package initialization
├── schema.py            # Database schema and initialization
├── parser.py            # MapServer JSON parser
├── indexer.py           # Database indexing from JSON files
├── search.py            # Search and query interface
├── cli.py               # Command-line interface
└── README.md            # This file
```

## Architecture

### Data Flow

1. **Indexing Phase**
   - `indexer.py` scans data directory for `*_MapServer.json` files
   - `parser.py` extracts metadata from each JSON file
   - Data is normalized and inserted into SQLite tables
   - Full-text search index is automatically updated via triggers

2. **Search Phase**
   - `search.py` provides query methods
   - Queries use indexes for fast retrieval
   - Results are returned as dictionaries
   - `cli.py` formats output for display

### Key Components

- **MapServerParser**: Extracts structured metadata from JSON files
- **MapServerIndexer**: Populates database from JSON files
- **MapServiceCatalog**: Provides search and query interface
- **CLI**: User-friendly command-line interface

## Performance

- **Full-text search** uses SQLite FTS5 for fast text queries
- **Indexes** on commonly-searched fields (folder, keyword, geometry type)
- **Efficient storage** with normalized keyword table
- Can handle thousands of map services efficiently

## Examples

### Example 1: Find all fire-related services

```bash
python -m dbsearch.cli search "fire" --limit 20
```

### Example 2: Explore services by folder

```bash
# List all folders
python -m dbsearch.cli list-folders

# Browse EDW folder
python -m dbsearch.cli folder EDW
```

### Example 3: Find polygon services with keyword "silviculture"

```python
from dbsearch.schema import init_database
from dbsearch.search import MapServiceCatalog

conn = init_database()
catalog = MapServiceCatalog(conn)

# Find by keyword
keyword_results = catalog.search_by_keyword("silviculture")

# Filter by geometry type
polygon_services = [
    s for s in keyword_results
    if any(
        layer['geometry_type'] == 'esriGeometryPolygon'
        for layer in catalog.get_service_layers(s['id'])
    )
]

for service in polygon_services:
    print(service['title'])
```

### Example 4: Export search results to JSON

```bash
python -m dbsearch.cli search "FACTS" --format json > results.json
```

## Extending the System

### Adding New Search Methods

Add new search methods to `search.py`:

```python
def find_by_author(self, author: str, limit: int = 100):
    """Find services by author."""
    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT * FROM mapservices
        WHERE author LIKE ?
        LIMIT ?
    """, (f'%{author}%', limit))
    return [dict(row) for row in cursor.fetchall()]
```

### Adding New CLI Commands

Add new commands to `cli.py`:

```python
def cmd_author(args):
    """Search by author."""
    conn = init_database(args.db)
    catalog = MapServiceCatalog(conn)
    results = catalog.find_by_author(args.author, limit=args.limit)
    # ... format and display results
```

## Troubleshooting

### Database locked errors
If you get "database is locked" errors, ensure no other processes are accessing the database.

### Missing services after indexing
Check that your JSON files match the pattern `*_MapServer.json`.

### Slow searches
The database includes indexes on common search fields. If searches are slow, ensure the database file isn't on a network drive.

## License

This module is part of the catalog-open-data project.
