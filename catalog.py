"""
Catalog Librarian relational schema.

This module implements a SQLite schema and light-weight repository helpers for the
AI-powered "Catalog Librarian" described in ``catalog-ideas.md``.  The schema
captures dataset metadata, lineage, dashboard suitability scores, evidence
snippets, embeddings, and natural-language query logs so downstream components
can answer lineage questions, recommend datasets for dashboards (e.g., timber
harvesting or wildfire risk), and ground LLM responses in real MapServer data.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence, Tuple
import sys

PROJECT_SRC = Path(__file__).parent / "src"
if PROJECT_SRC.exists() and str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

try:
    from rich import print as rprint
except ModuleNotFoundError:  # pragma: no cover - fallback when rich is absent
    def rprint(*args, **kwargs):
        print(*args, **kwargs)

from catalog_open_data.schema import Layer as MapLayer
from catalog_open_data.schema import MapServer

CATALOG_DB_PATH = Path("data/catalog.db")

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        summary TEXT,
        service_description TEXT,
        service_url TEXT,
        service_type TEXT,
        mapserver_path TEXT,
        geographic_scope TEXT,
        update_frequency TEXT,
        document_keywords TEXT,
        lineage_status TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS layers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id INTEGER NOT NULL,
        layer_name TEXT NOT NULL,
        description TEXT,
        geometry_type TEXT,
        default_visibility INTEGER DEFAULT 1 CHECK (default_visibility IN (0, 1)),
        min_scale REAL,
        max_scale REAL,
        keywords TEXT,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS lineage_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        source_name TEXT,
        source_url TEXT,
        notes TEXT,
        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS dataset_dependencies (
        dataset_id INTEGER NOT NULL,
        depends_on_dataset_id INTEGER NOT NULL,
        relationship_type TEXT DEFAULT 'source',
        notes TEXT,
        PRIMARY KEY(dataset_id, depends_on_dataset_id),
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
        FOREIGN KEY(depends_on_dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS use_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS dataset_use_cases (
        dataset_id INTEGER NOT NULL,
        use_case_id INTEGER NOT NULL,
        suitability_score REAL CHECK (suitability_score BETWEEN 0 AND 1),
        rationale TEXT,
        PRIMARY KEY(dataset_id, use_case_id),
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
        FOREIGN KEY(use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        value TEXT NOT NULL UNIQUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS dataset_keywords (
        dataset_id INTEGER NOT NULL,
        keyword_id INTEGER NOT NULL,
        PRIMARY KEY(dataset_id, keyword_id),
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
        FOREIGN KEY(keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence_snippets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id INTEGER NOT NULL,
        snippet_type TEXT NOT NULL,
        content TEXT NOT NULL,
        source_pointer TEXT,
        metadata_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS dataset_embeddings (
        dataset_id INTEGER PRIMARY KEY,
        provider TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        vector TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS nl_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        intent TEXT,
        dataset_id INTEGER,
        response_summary TEXT,
        asked_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE SET NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_layers_dataset_id ON layers(dataset_id);",
    "CREATE INDEX IF NOT EXISTS idx_lineage_dataset ON lineage_events(dataset_id);",
    "CREATE INDEX IF NOT EXISTS idx_dataset_use_cases_use_case ON dataset_use_cases(use_case_id);",
    "CREATE INDEX IF NOT EXISTS idx_dataset_keywords_keyword ON dataset_keywords(keyword_id);",
]


def _split_keywords(value: str | None) -> list[str]:
    """Split comma-separated keywords while keeping the result normalized."""

    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _layer_to_kwargs(layer: MapLayer) -> dict:
    """Translate a MapServer layer into parameters for ``add_layer``."""

    return {
        "name": layer.name or f"Layer {layer.id}",
        "description": None,
        "geometry_type": layer.type,
        "default_visibility": (layer.defaultVisibility is not False),
        "min_scale": layer.minScale,
        "max_scale": layer.maxScale,
        "keywords": _split_keywords(layer.name),
    }


@dataclass(frozen=True)
class UseCaseSeed:
    """Seed data for high-priority dashboard scenarios."""

    slug: str
    name: str
    description: str


DEFAULT_USE_CASES: Sequence[UseCaseSeed] = (
    UseCaseSeed(
        slug="timber-harvest-dashboard",
        name="Timber Harvesting Dashboard",
        description=(
            "Surfacing silviculture, timber stand improvement, and harvest activity "
            "layers needed for timber dashboard recommendations."
        ),
    ),
    UseCaseSeed(
        slug="wildfire-risk-dashboard",
        name="Wildfire Risk Dashboard",
        description=(
            "Aggregates fuels, fire occurrence, and hazard potential layers so the "
            "librarian can answer wildfire risk questions."
        ),
    ),
    UseCaseSeed(
        slug="data-lineage-trace",
        name="Data Lineage Trace",
        description=(
            "Captures provenance hops (MapServer metadata, processing steps, "
            "external APIs) to power lineage explanations."
        ),
    ),
)


class CatalogDatabase:
    """
    Thin repository for managing the catalog schema.

    It centralizes dataset metadata, lineage events, dashboard suitability, and
    query logs so the rest of the tooling (LLMs, retrieval pipelines, CLI) can
    fetch structured context without re-deriving relationships.
    """

    def __init__(self, db_path: Path | str = CATALOG_DB_PATH):
        self.db_path = Path(db_path)
        if self.db_path.parent and not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON;")

    def __enter__(self) -> "CatalogDatabase":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying SQLite connection."""

        if self.connection:
            self.connection.close()

    def initialize(self) -> None:
        """Create all tables, indexes, and helper structures."""

        for statement in SCHEMA_STATEMENTS:
            stmt = statement.strip()
            if not stmt:
                continue
            self.connection.executescript(f"{stmt}\n")
        self.connection.commit()

    def seed_use_cases(
        self, seeds: Sequence[UseCaseSeed] = DEFAULT_USE_CASES
    ) -> int:
        """
        Ensure baseline dashboard/use-case records exist.

        Returns:
            int: Number of use-case rows inserted or updated.
        """

        before = self.connection.total_changes
        cursor = self.connection.cursor()
        for seed in seeds:
            cursor.execute(
                """
                INSERT INTO use_cases (slug, name, description)
                VALUES (:slug, :name, :description)
                ON CONFLICT(slug) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description
                """,
                {
                    "slug": seed.slug,
                    "name": seed.name,
                    "description": seed.description,
                },
            )
        self.connection.commit()
        return self.connection.total_changes - before

    def register_dataset(
        self,
        *,
        slug: str,
        title: str,
        summary: str | None = None,
        service_description: str | None = None,
        service_url: str | None = None,
        service_type: str | None = None,
        mapserver_path: str | None = None,
        geographic_scope: str | None = None,
        update_frequency: str | None = None,
        document_keywords: str | None = None,
        lineage_status: str | None = None,
    ) -> int:
        """
        Insert or update a dataset record.

        Returns:
            int: Database ID for the dataset, useful for follow-up inserts.
        """

        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM datasets WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        payload = {
            "slug": slug,
            "title": title,
            "summary": summary,
            "service_description": service_description,
            "service_url": service_url,
            "service_type": service_type,
            "mapserver_path": mapserver_path,
            "geographic_scope": geographic_scope,
            "update_frequency": update_frequency,
            "document_keywords": document_keywords,
            "lineage_status": lineage_status,
        }

        if row:
            dataset_id = row["id"]
            cursor.execute(
                """
                UPDATE datasets
                SET title = :title,
                    summary = :summary,
                    service_description = :service_description,
                    service_url = :service_url,
                    service_type = :service_type,
                    mapserver_path = :mapserver_path,
                    geographic_scope = :geographic_scope,
                    update_frequency = :update_frequency,
                    document_keywords = :document_keywords,
                    lineage_status = :lineage_status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :dataset_id
                """,
                {**payload, "dataset_id": dataset_id},
            )
        else:
            cursor.execute(
                """
                INSERT INTO datasets (
                    slug,
                    title,
                    summary,
                    service_description,
                    service_url,
                    service_type,
                    mapserver_path,
                    geographic_scope,
                    update_frequency,
                    document_keywords,
                    lineage_status
                )
                VALUES (
                    :slug,
                    :title,
                    :summary,
                    :service_description,
                    :service_url,
                    :service_type,
                    :mapserver_path,
                    :geographic_scope,
                    :update_frequency,
                    :document_keywords,
                    :lineage_status
                )
                """,
                payload,
            )
            dataset_id = cursor.lastrowid

        self.connection.commit()
        return dataset_id

    def register_mapserver_dataset(
        self,
        slug: str,
        mapserver: MapServer,
        *,
        mapserver_path: str | None = None,
        service_url: str | None = None,
        use_case_scores: Sequence[Tuple[str, float, str | None]] = (),
    ) -> int:
        """
        Convenience wrapper that projects a MapServer object into catalog tables.

        Args:
            slug: Stable identifier (e.g., derived from folder/name).
            mapserver: Pydantic MapServer model from ``schema.py``.
            mapserver_path: Optional path to the source JSON on disk.
            service_url: Authoritative REST endpoint, if known.
            use_case_scores: Optional iterable of (use_case_slug, score, rationale).
        """

        document_info = mapserver.documentInfo
        title = mapserver.mapName or (document_info.Title if document_info else None)
        title = title or slug.replace("-", " ").title()
        summary = (
            mapserver.description
            or mapserver.serviceDescription
            or (document_info.Comments if document_info else None)
        )

        dataset_id = self.register_dataset(
            slug=slug,
            title=title,
            summary=summary,
            service_description=mapserver.serviceDescription,
            service_url=service_url,
            service_type="MapServer",
            mapserver_path=mapserver_path,
            geographic_scope=(document_info.Subject if document_info else None),
            update_frequency=None,
            document_keywords=(
                document_info.Keywords if document_info else None
            ),
            lineage_status=(
                document_info.Category if document_info else None
            ),
        )

        keyword_values = _split_keywords(
            document_info.Keywords if document_info else None
        )
        if keyword_values:
            self.register_keywords(dataset_id, keyword_values)

        for layer in mapserver.layers or []:
            self.add_layer(dataset_id, **_layer_to_kwargs(layer))

        for use_case_slug, score, rationale in use_case_scores:
            self.link_dataset_to_use_case(
                dataset_id,
                use_case_slug=use_case_slug,
                suitability_score=score,
                rationale=rationale,
            )

        return dataset_id

    def add_layer(
        self,
        dataset_id: int,
        *,
        name: str,
        description: str | None = None,
        geometry_type: str | None = None,
        default_visibility: bool = True,
        min_scale: float | None = None,
        max_scale: float | None = None,
        keywords: Iterable[str] | None = None,
    ) -> int:
        """Persist a layer definition tied to a dataset."""

        keyword_blob = None
        if keywords:
            keyword_blob = ", ".join(sorted({kw.strip() for kw in keywords if kw}))

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO layers (
                dataset_id,
                layer_name,
                description,
                geometry_type,
                default_visibility,
                min_scale,
                max_scale,
                keywords
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                name,
                description,
                geometry_type,
                int(default_visibility),
                min_scale,
                max_scale,
                keyword_blob,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def register_keywords(
        self, dataset_id: int, keywords: Iterable[str]
    ) -> None:
        """Attach normalized keywords to a dataset."""

        normalized = sorted(
            {kw.strip().lower() for kw in keywords if kw and kw.strip()}
        )
        if not normalized:
            return

        cursor = self.connection.cursor()
        for keyword in normalized:
            cursor.execute(
                "INSERT OR IGNORE INTO keywords (value) VALUES (?)", (keyword,)
            )
            cursor.execute(
                """
                INSERT OR IGNORE INTO dataset_keywords (dataset_id, keyword_id)
                SELECT ?, id FROM keywords WHERE value = ?
                """,
                (dataset_id, keyword),
            )

        self.connection.commit()

    def record_lineage_event(
        self,
        dataset_id: int,
        *,
        event_type: str,
        source_name: str | None = None,
        source_url: str | None = None,
        notes: str | None = None,
    ) -> int:
        """Capture provenance steps for lineage queries."""

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO lineage_events (
                dataset_id,
                event_type,
                source_name,
                source_url,
                notes
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (dataset_id, event_type, source_name, source_url, notes),
        )
        self.connection.commit()
        return cursor.lastrowid

    def link_dataset_dependency(
        self,
        dataset_id: int,
        depends_on_dataset_id: int,
        *,
        relationship_type: str = "source",
        notes: str | None = None,
    ) -> None:
        """Document dataset-to-dataset lineage relationships."""

        self.connection.execute(
            """
            INSERT OR REPLACE INTO dataset_dependencies (
                dataset_id,
                depends_on_dataset_id,
                relationship_type,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (dataset_id, depends_on_dataset_id, relationship_type, notes),
        )
        self.connection.commit()

    def link_dataset_to_use_case(
        self,
        dataset_id: int,
        *,
        use_case_slug: str,
        suitability_score: float,
        rationale: str | None = None,
    ) -> None:
        """Store suitability scores for a dataset/use-case pair."""

        use_case_id = self._resolve_use_case_id(use_case_slug)
        if use_case_id is None:
            raise ValueError(f"Unknown use-case slug: {use_case_slug}")

        self.connection.execute(
            """
            INSERT INTO dataset_use_cases (
                dataset_id,
                use_case_id,
                suitability_score,
                rationale
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(dataset_id, use_case_id) DO UPDATE SET
                suitability_score = excluded.suitability_score,
                rationale = excluded.rationale
            """,
            (dataset_id, use_case_id, suitability_score, rationale),
        )
        self.connection.commit()

    def register_evidence_snippet(
        self,
        dataset_id: int,
        *,
        snippet_type: str,
        content: str,
        source_pointer: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """Persist snippets that LLM answers can cite."""

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO evidence_snippets (
                dataset_id,
                snippet_type,
                content,
                source_pointer,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                snippet_type,
                content,
                source_pointer,
                json.dumps(metadata or {}),
            ),
        )
        self.connection.commit()
        return cursor.lastrowid

    def store_embedding(
        self,
        dataset_id: int,
        *,
        provider: str,
        vector: Sequence[float],
    ) -> None:
        """Persist semantic embeddings to support RAG lookups."""

        payload = {
            "dataset_id": dataset_id,
            "provider": provider,
            "dimensions": len(vector),
            "vector": json.dumps(list(vector)),
        }
        self.connection.execute(
            """
            INSERT INTO dataset_embeddings (
                dataset_id,
                provider,
                dimensions,
                vector
            )
            VALUES (
                :dataset_id,
                :provider,
                :dimensions,
                :vector
            )
            ON CONFLICT(dataset_id) DO UPDATE SET
                provider = excluded.provider,
                dimensions = excluded.dimensions,
                vector = excluded.vector,
                created_at = CURRENT_TIMESTAMP
            """,
            payload,
        )
        self.connection.commit()

    def log_nl_query(
        self,
        question: str,
        *,
        intent: str | None = None,
        dataset_id: int | None = None,
        response_summary: str | None = None,
    ) -> int:
        """Track natural-language interactions for observability."""

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO nl_queries (
                question,
                intent,
                dataset_id,
                response_summary
            )
            VALUES (?, ?, ?, ?)
            """,
            (question, intent, dataset_id, response_summary),
        )
        self.connection.commit()
        return cursor.lastrowid

    def _resolve_use_case_id(self, slug: str) -> int | None:
        cursor = self.connection.execute(
            "SELECT id FROM use_cases WHERE slug = ?", (slug,)
        )
        row = cursor.fetchone()
        return row["id"] if row else None


def load_mapserver_from_file(path: Path | str) -> MapServer:
    """Load and validate a MapServer JSON file using existing Pydantic models."""

    with open(path, "r", encoding="utf-8") as fp:
        json_data = json.load(fp)
    return MapServer.model_validate(json_data)


def main() -> None:
    """
    Initialize the schema and showcase a reference dataset entry.

    Running this module directly will create ``data/catalog.db`` (if needed),
    install the schema, seed baseline use cases, and insert a reference record
    for the 2023 Wildfire Hazard Potential MapServer that already exists under
    ``data/``.  This demonstrates how the schema supports lineage tracking and
    dashboard recommendations without wiring up the full ingestion pipeline yet.
    """

    with CatalogDatabase() as catalog_db:
        catalog_db.initialize()
        changed = catalog_db.seed_use_cases()

        example_path = Path(
            "data/apps.fs.usda.gov.arcx.rest.services/RDW_Wildfire/"
            "RMRS_WildfireHazardPotential_2023_MapServer.json"
        )
        if example_path.exists():
            mapserver = load_mapserver_from_file(example_path)
            dataset_id = catalog_db.register_mapserver_dataset(
                "rmrs-wildfire-hazard-potential-2023",
                mapserver,
                mapserver_path=str(example_path),
                service_url=(
                    "https://apps.fs.usda.gov/arcx/rest/services/"
                    "RDW_Wildfire/RMRS_WildfireHazardPotential_2023_MapServer"
                ),
                use_case_scores=[
                    (
                        "wildfire-risk-dashboard",
                        0.95,
                        (
                            "Raster hazard classes directly support wildfire risk "
                            "dashboards described in catalog-ideas.md."
                        ),
                    )
                ],
            )

            catalog_db.record_lineage_event(
                dataset_id,
                event_type="ingest",
                source_name="USDA Forest Service RDW Wildfire",
                source_url=(
                    "https://apps.fs.usda.gov/arcx/rest/services/RDW_Wildfire/"
                    "RMRS_WildfireHazardPotential_2023_MapServer"
                ),
                notes="Loaded MapServer metadata into local catalog cache.",
            )

        rprint(
            "[bold green]Catalog schema ready:[/bold green] "
            f"{catalog_db.db_path} (seed changes: {changed})"
        )


if __name__ == "__main__":
    main()
