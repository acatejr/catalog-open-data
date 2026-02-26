"""
Parser for MapServer JSON metadata files.
"""

import json
from pathlib import Path
from typing import Any


class MapServerParser:
    """Parse MapServer JSON metadata files."""

    def __init__(self, json_path: str | Path):
        """
        Initialize parser with a JSON file path.

        Args:
            json_path: Path to the MapServer JSON file
        """
        self.json_path = Path(json_path)
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data: dict[str, Any] = json.load(f)

    def get_map_name(self) -> str:
        """Extract the map service name."""
        return self.data.get('mapName', '')

    def get_title(self) -> str:
        """Extract the service title from documentInfo."""
        doc_info = self.data.get('documentInfo', {})
        return doc_info.get('Title', '')

    def get_service_description(self) -> str:
        """Extract the service description."""
        return self.data.get('serviceDescription', '')

    def get_subject(self) -> str:
        """Extract the subject from documentInfo."""
        doc_info = self.data.get('documentInfo', {})
        return doc_info.get('Subject', '')

    def get_keywords(self) -> str:
        """Extract keywords from documentInfo as a comma-separated string."""
        doc_info = self.data.get('documentInfo', {})
        return doc_info.get('Keywords', '')

    def get_keywords_list(self) -> list[str]:
        """Extract keywords as a list."""
        keywords_str = self.get_keywords()
        if not keywords_str:
            return []
        # Split by comma and strip whitespace
        return [kw.strip() for kw in keywords_str.split(',') if kw.strip()]

    def get_author(self) -> str:
        """Extract the author from documentInfo."""
        doc_info = self.data.get('documentInfo', {})
        return doc_info.get('Author', '')

    def get_version(self) -> str:
        """Extract the version from documentInfo."""
        doc_info = self.data.get('documentInfo', {})
        return doc_info.get('Version', '')

    def get_capabilities(self) -> str:
        """Extract capabilities as a comma-separated string."""
        return self.data.get('capabilities', '')

    def get_spatial_reference_wkid(self) -> int | None:
        """Extract the WKID (Well-Known ID) of the spatial reference."""
        spatial_ref = self.data.get('spatialReference', {})
        return spatial_ref.get('wkid') or spatial_ref.get('latestWkid')

    def get_min_scale(self) -> float | None:
        """Extract the minimum scale."""
        return self.data.get('minScale')

    def get_max_scale(self) -> float | None:
        """Extract the maximum scale."""
        return self.data.get('maxScale')

    def get_full_extent(self) -> dict[str, float | None]:
        """
        Extract the full extent bounding box.

        Returns:
            Dictionary with xmin, ymin, xmax, ymax keys
        """
        full_extent = self.data.get('fullExtent', {})
        return {
            'xmin': full_extent.get('xmin'),
            'ymin': full_extent.get('ymin'),
            'xmax': full_extent.get('xmax'),
            'ymax': full_extent.get('ymax')
        }

    def get_folder_path(self) -> str:
        """
        Extract folder path from the file path.

        Example: data/.../EDW/EDW_Service.json -> "EDW"
        """
        # Get the parent directory name before the filename
        parts = self.json_path.parts
        # Find the folder between the base services path and the filename
        for i, part in enumerate(parts):
            if 'arcx.rest.services' in part:
                # The next part should be the folder name (e.g., "EDW")
                if i + 1 < len(parts) - 1:  # Make sure there's a folder before the file
                    return parts[i + 1]
        return ''

    def get_layers(self) -> list[dict[str, Any]]:
        """
        Extract layer information.

        Returns:
            List of dictionaries containing layer metadata
        """
        layers = self.data.get('layers', [])
        result = []
        for layer in layers:
            result.append({
                'layer_id': layer.get('id'),
                'layer_name': layer.get('name', ''),
                'geometry_type': layer.get('geometryType', ''),
                'layer_type': layer.get('type', ''),
                'min_scale': layer.get('minScale'),
                'max_scale': layer.get('maxScale')
            })
        return result

    def to_dict(self) -> dict[str, Any]:
        """
        Convert all parsed metadata to a dictionary.

        Returns:
            Dictionary containing all extracted metadata
        """
        extent = self.get_full_extent()
        return {
            'map_name': self.get_map_name(),
            'title': self.get_title(),
            'service_description': self.get_service_description(),
            'subject': self.get_subject(),
            'keywords': self.get_keywords(),
            'author': self.get_author(),
            'version': self.get_version(),
            'capabilities': self.get_capabilities(),
            'spatial_reference_wkid': self.get_spatial_reference_wkid(),
            'min_scale': self.get_min_scale(),
            'max_scale': self.get_max_scale(),
            'extent_xmin': extent['xmin'],
            'extent_ymin': extent['ymin'],
            'extent_xmax': extent['xmax'],
            'extent_ymax': extent['ymax'],
            'folder_path': self.get_folder_path(),
            'file_path': str(self.json_path),
            'layers': self.get_layers(),
            'keywords_list': self.get_keywords_list()
        }
