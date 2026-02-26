"""
MapServer Catalog Database Search Module

This module provides a searchable catalog for USDA Forest Service MapServer metadata.
"""

from dbsearch.schema import init_database
from dbsearch.search import MapServiceCatalog

__all__ = ['init_database', 'MapServiceCatalog']
