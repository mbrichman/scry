"""
Import system with pluggable format extractors.

This module provides a registry-based system for detecting and extracting
different chat export formats (ChatGPT, Claude, OpenWebUI, etc.).

Extractors are dynamically discovered from the db/importers/ directory
without requiring manual registry updates.
"""

from db.importers.registry import detect_format, FORMAT_REGISTRY, EXTRACTOR_METADATA
from db.importers.loader import discover_extractors

__all__ = ["detect_format", "FORMAT_REGISTRY", "EXTRACTOR_METADATA", "discover_extractors"]
