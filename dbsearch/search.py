"""
Search and query functions for the MapServer catalog.
"""

import sqlite3
from typing import Any


class MapServiceCatalog:
    """Search and query interface for the MapServer catalog."""

    def __init__(self, db_conn: sqlite3.Connection):
        """
        Initialize the catalog with a database connection.

        Args:
            db_conn: SQLite database connection
        """
        self.conn = db_conn
        self.conn.row_factory = sqlite3.Row

    def search(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Full-text search across service names, titles, descriptions, and keywords.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching mapservices
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*
            FROM mapservices m
            JOIN mapservices_fts fts ON m.id = fts.rowid
            WHERE mapservices_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))

        return [dict(row) for row in cursor.fetchall()]

    def search_by_keyword(self, keyword: str, exact: bool = False, limit: int = 100) -> list[dict[str, Any]]:
        """
        Search for services by keyword.

        Args:
            keyword: Keyword to search for
            exact: If True, match exact keyword; if False, use partial match
            limit: Maximum number of results to return

        Returns:
            List of matching mapservices
        """
        cursor = self.conn.cursor()

        if exact:
            cursor.execute("""
                SELECT DISTINCT m.*
                FROM mapservices m
                JOIN keywords k ON m.id = k.mapservice_id
                WHERE k.keyword = ?
                LIMIT ?
            """, (keyword, limit))
        else:
            cursor.execute("""
                SELECT DISTINCT m.*
                FROM mapservices m
                JOIN keywords k ON m.id = k.mapservice_id
                WHERE k.keyword LIKE ?
                LIMIT ?
            """, (f'%{keyword}%', limit))

        return [dict(row) for row in cursor.fetchall()]

    def find_by_geometry_type(self, geometry_type: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Find services by geometry type.

        Args:
            geometry_type: Geometry type (e.g., "esriGeometryPolygon", "esriGeometryPoint")
            limit: Maximum number of results to return

        Returns:
            List of matching mapservices
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT m.*
            FROM mapservices m
            JOIN layers l ON m.id = l.mapservice_id
            WHERE l.geometry_type = ?
            LIMIT ?
        """, (geometry_type, limit))

        return [dict(row) for row in cursor.fetchall()]

    def find_by_capability(self, capability: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Find services by capability.

        Args:
            capability: Capability to search for (e.g., "Query", "Data", "Map")
            limit: Maximum number of results to return

        Returns:
            List of matching mapservices
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM mapservices
            WHERE capabilities LIKE ?
            LIMIT ?
        """, (f'%{capability}%', limit))

        return [dict(row) for row in cursor.fetchall()]

    def find_by_spatial_extent(
        self,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Find services that intersect with a given bounding box.

        Args:
            xmin: Minimum X coordinate
            ymin: Minimum Y coordinate
            xmax: Maximum X coordinate
            ymax: Maximum Y coordinate
            limit: Maximum number of results to return

        Returns:
            List of matching mapservices
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM mapservices
            WHERE extent_xmin <= ? AND extent_xmax >= ?
              AND extent_ymin <= ? AND extent_ymax >= ?
            LIMIT ?
        """, (xmax, xmin, ymax, ymin, limit))

        return [dict(row) for row in cursor.fetchall()]

    def find_by_folder(self, folder_name: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Find services in a specific folder.

        Args:
            folder_name: Name of the folder (e.g., "EDW")
            limit: Maximum number of results to return

        Returns:
            List of matching mapservices
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM mapservices
            WHERE folder_path = ?
            LIMIT ?
        """, (folder_name, limit))

        return [dict(row) for row in cursor.fetchall()]

    def get_service_by_name(self, map_name: str) -> dict[str, Any] | None:
        """
        Get a specific service by its map name.

        Args:
            map_name: The map service name

        Returns:
            Service details or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM mapservices
            WHERE map_name = ?
        """, (map_name,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_service_layers(self, mapservice_id: int) -> list[dict[str, Any]]:
        """
        Get all layers for a specific service.

        Args:
            mapservice_id: The mapservice ID

        Returns:
            List of layers
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM layers
            WHERE mapservice_id = ?
            ORDER BY layer_id
        """, (mapservice_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_service_keywords(self, mapservice_id: int) -> list[str]:
        """
        Get all keywords for a specific service.

        Args:
            mapservice_id: The mapservice ID

        Returns:
            List of keywords
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT keyword
            FROM keywords
            WHERE mapservice_id = ?
            ORDER BY keyword
        """, (mapservice_id,))

        return [row['keyword'] for row in cursor.fetchall()]

    def list_all_folders(self) -> list[str]:
        """
        Get a list of all unique folder names.

        Returns:
            List of folder names
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT folder_path
            FROM mapservices
            WHERE folder_path IS NOT NULL AND folder_path != ''
            ORDER BY folder_path
        """)

        return [row['folder_path'] for row in cursor.fetchall()]

    def list_all_keywords(self) -> list[tuple[str, int]]:
        """
        Get a list of all unique keywords with their usage counts.

        Returns:
            List of tuples (keyword, count)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT keyword, COUNT(*) as count
            FROM keywords
            GROUP BY keyword
            ORDER BY count DESC, keyword
        """)

        return [(row['keyword'], row['count']) for row in cursor.fetchall()]

    def browse_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """
        Browse all services with pagination.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of mapservices
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM mapservices
            ORDER BY map_name
            LIMIT ? OFFSET ?
        """, (limit, offset))

        return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict[str, int]:
        """
        Get catalog statistics.

        Returns:
            Dictionary with catalog statistics
        """
        cursor = self.conn.cursor()

        # Count services
        cursor.execute("SELECT COUNT(*) as count FROM mapservices")
        service_count = cursor.fetchone()['count']

        # Count layers
        cursor.execute("SELECT COUNT(*) as count FROM layers")
        layer_count = cursor.fetchone()['count']

        # Count unique keywords
        cursor.execute("SELECT COUNT(DISTINCT keyword) as count FROM keywords")
        keyword_count = cursor.fetchone()['count']

        # Count folders
        cursor.execute("""
            SELECT COUNT(DISTINCT folder_path) as count
            FROM mapservices
            WHERE folder_path IS NOT NULL AND folder_path != ''
        """)
        folder_count = cursor.fetchone()['count']

        return {
            'total_services': service_count,
            'total_layers': layer_count,
            'unique_keywords': keyword_count,
            'folders': folder_count
        }
