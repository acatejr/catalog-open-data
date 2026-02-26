"""
Database schema for MapServer catalog.
"""

import sqlite3
from pathlib import Path


def init_database(db_path: str = "mapserver_catalog.db") -> sqlite3.Connection:
    """
    Initialize the SQLite database with the catalog schema.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        Database connection object
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create mapservices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mapservices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            map_name TEXT NOT NULL UNIQUE,
            title TEXT,
            service_description TEXT,
            subject TEXT,
            keywords TEXT,
            author TEXT,
            version TEXT,
            capabilities TEXT,
            spatial_reference_wkid INTEGER,
            min_scale REAL,
            max_scale REAL,
            extent_xmin REAL,
            extent_ymin REAL,
            extent_xmax REAL,
            extent_ymax REAL,
            folder_path TEXT,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create layers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS layers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mapservice_id INTEGER NOT NULL,
            layer_id INTEGER NOT NULL,
            layer_name TEXT,
            geometry_type TEXT,
            layer_type TEXT,
            min_scale REAL,
            max_scale REAL,
            FOREIGN KEY (mapservice_id) REFERENCES mapservices(id) ON DELETE CASCADE
        )
    """)

    # Create keywords table (normalized)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mapservice_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            FOREIGN KEY (mapservice_id) REFERENCES mapservices(id) ON DELETE CASCADE
        )
    """)

    # Create indexes for common search patterns
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mapservices_map_name
        ON mapservices(map_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mapservices_folder
        ON mapservices(folder_path)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_keywords_keyword
        ON keywords(keyword)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_layers_geometry_type
        ON layers(geometry_type)
    """)

    # Create full-text search virtual table
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS mapservices_fts USING fts5(
            map_name,
            title,
            service_description,
            keywords,
            content='mapservices',
            content_rowid='id'
        )
    """)

    # Create triggers to keep FTS table in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS mapservices_ai AFTER INSERT ON mapservices BEGIN
            INSERT INTO mapservices_fts(rowid, map_name, title, service_description, keywords)
            VALUES (new.id, new.map_name, new.title, new.service_description, new.keywords);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS mapservices_ad AFTER DELETE ON mapservices BEGIN
            DELETE FROM mapservices_fts WHERE rowid = old.id;
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS mapservices_au AFTER UPDATE ON mapservices BEGIN
            UPDATE mapservices_fts
            SET map_name = new.map_name,
                title = new.title,
                service_description = new.service_description,
                keywords = new.keywords
            WHERE rowid = new.id;
        END
    """)

    conn.commit()
    return conn


def clear_database(conn: sqlite3.Connection):
    """Clear all data from the database tables."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keywords")
    cursor.execute("DELETE FROM layers")
    cursor.execute("DELETE FROM mapservices")
    conn.commit()
