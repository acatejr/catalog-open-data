"""
Indexer for building the MapServer catalog database from JSON files.
"""

import sqlite3
from pathlib import Path
from typing import Iterator

from dbsearch.parser import MapServerParser


class MapServerIndexer:
    """Index MapServer JSON files into the catalog database."""

    def __init__(self, db_conn: sqlite3.Connection):
        """
        Initialize the indexer with a database connection.

        Args:
            db_conn: SQLite database connection
        """
        self.conn = db_conn
        self.cursor = db_conn.cursor()

    def find_json_files(self, data_dir: str | Path) -> Iterator[Path]:
        """
        Find all MapServer JSON files in the data directory.

        Args:
            data_dir: Path to the data directory

        Yields:
            Path objects for each JSON file found
        """
        data_path = Path(data_dir)
        if not data_path.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        # Find all JSON files that end with _MapServer.json
        yield from data_path.rglob("*_MapServer.json")

    def index_file(self, json_path: Path) -> int | None:
        """
        Index a single MapServer JSON file.

        Args:
            json_path: Path to the JSON file

        Returns:
            The mapservice_id of the inserted record, or None if failed
        """
        try:
            parser = MapServerParser(json_path)
            metadata = parser.to_dict()

            # Check if this service already exists
            self.cursor.execute(
                "SELECT id FROM mapservices WHERE map_name = ?",
                (metadata['map_name'],)
            )
            existing = self.cursor.fetchone()

            if existing:
                # Update existing record
                mapservice_id = existing[0]
                self.cursor.execute("""
                    UPDATE mapservices
                    SET title = ?,
                        service_description = ?,
                        subject = ?,
                        keywords = ?,
                        author = ?,
                        version = ?,
                        capabilities = ?,
                        spatial_reference_wkid = ?,
                        min_scale = ?,
                        max_scale = ?,
                        extent_xmin = ?,
                        extent_ymin = ?,
                        extent_xmax = ?,
                        extent_ymax = ?,
                        folder_path = ?,
                        file_path = ?
                    WHERE id = ?
                """, (
                    metadata['title'],
                    metadata['service_description'],
                    metadata['subject'],
                    metadata['keywords'],
                    metadata['author'],
                    metadata['version'],
                    metadata['capabilities'],
                    metadata['spatial_reference_wkid'],
                    metadata['min_scale'],
                    metadata['max_scale'],
                    metadata['extent_xmin'],
                    metadata['extent_ymin'],
                    metadata['extent_xmax'],
                    metadata['extent_ymax'],
                    metadata['folder_path'],
                    metadata['file_path'],
                    mapservice_id
                ))

                # Delete old layers and keywords
                self.cursor.execute("DELETE FROM layers WHERE mapservice_id = ?", (mapservice_id,))
                self.cursor.execute("DELETE FROM keywords WHERE mapservice_id = ?", (mapservice_id,))
            else:
                # Insert new mapservice record
                self.cursor.execute("""
                    INSERT INTO mapservices (
                        map_name, title, service_description, subject, keywords,
                        author, version, capabilities, spatial_reference_wkid,
                        min_scale, max_scale, extent_xmin, extent_ymin,
                        extent_xmax, extent_ymax, folder_path, file_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata['map_name'],
                    metadata['title'],
                    metadata['service_description'],
                    metadata['subject'],
                    metadata['keywords'],
                    metadata['author'],
                    metadata['version'],
                    metadata['capabilities'],
                    metadata['spatial_reference_wkid'],
                    metadata['min_scale'],
                    metadata['max_scale'],
                    metadata['extent_xmin'],
                    metadata['extent_ymin'],
                    metadata['extent_xmax'],
                    metadata['extent_ymax'],
                    metadata['folder_path'],
                    metadata['file_path']
                ))
                mapservice_id = self.cursor.lastrowid

            # Insert layers
            for layer in metadata['layers']:
                self.cursor.execute("""
                    INSERT INTO layers (
                        mapservice_id, layer_id, layer_name, geometry_type,
                        layer_type, min_scale, max_scale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    mapservice_id,
                    layer['layer_id'],
                    layer['layer_name'],
                    layer['geometry_type'],
                    layer['layer_type'],
                    layer['min_scale'],
                    layer['max_scale']
                ))

            # Insert keywords
            for keyword in metadata['keywords_list']:
                self.cursor.execute("""
                    INSERT INTO keywords (mapservice_id, keyword)
                    VALUES (?, ?)
                """, (mapservice_id, keyword))

            return mapservice_id

        except Exception as e:
            print(f"Error indexing {json_path}: {e}")
            return None

    def index_directory(self, data_dir: str | Path, verbose: bool = True) -> dict[str, int]:
        """
        Index all MapServer JSON files in a directory.

        Args:
            data_dir: Path to the data directory
            verbose: Print progress information

        Returns:
            Dictionary with indexing statistics
        """
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0
        }

        if verbose:
            print(f"Scanning for MapServer JSON files in {data_dir}...")

        files = list(self.find_json_files(data_dir))
        stats['total'] = len(files)

        if verbose:
            print(f"Found {stats['total']} files to index")

        for json_file in files:
            if verbose:
                print(f"Indexing: {json_file.name}")

            result = self.index_file(json_file)
            if result:
                stats['success'] += 1
            else:
                stats['failed'] += 1

        # Commit all changes
        self.conn.commit()

        if verbose:
            print(f"\nIndexing complete:")
            print(f"  Total files: {stats['total']}")
            print(f"  Successfully indexed: {stats['success']}")
            print(f"  Failed: {stats['failed']}")

        return stats
