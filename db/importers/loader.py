"""
Plugin loader for dynamic extractor discovery and registration.

Discovers and loads extractor modules from the db/importers/ directory
without requiring manual registry updates.
"""

import importlib
import inspect
import logging
import os
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from db.importers.metadata import DEFAULT_METADATA

logger = logging.getLogger(__name__)


def discover_extractors() -> Dict[str, Dict[str, Any]]:
    """
    Discover all extractor modules in the db/importers/ directory.
    
    Automatically finds and loads extractor modules that:
    - Are Python files (.py) in the importers directory
    - Are not internal modules (__init__, registry, loader, interfaces, etc.)
    - Expose extract_messages() or extract_messages_from_file() functions
    
    Returns:
        Dict mapping format names to extractor info dicts:
        {
            'chatgpt': {
                'name': 'ChatGPT',
                'extract': <function>,
                'module': <module>
            },
            ...
        }
    """
    extractors = {}
    importers_dir = Path(__file__).parent
    
    # List of modules to skip
    skip_modules = {
        '__init__',
        '__pycache__',
        'registry',
        'loader',
        'interfaces',
        '.py',
    }
    
    # Iterate through Python files in importers directory
    for py_file in importers_dir.glob('*.py'):
        module_name = py_file.stem
        
        # Skip internal modules
        if module_name in skip_modules or module_name.startswith('_'):
            continue
        
        try:
            # Dynamically import the module
            module = importlib.import_module(f'db.importers.{module_name}')
            
            # Check if module has extract functions
            extract_func = _get_extract_function(module)
            if extract_func is None:
                continue
            
            # Determine format name (use module name, capitalize first letter)
            format_name = module_name.lower()
            display_name = module_name.replace('_', ' ').title()
            
            # Store extractor info
            extractors[format_name] = {
                'name': display_name,
                'extract': extract_func,
                'module': module,
                'metadata': _extract_metadata(module, format_name)
            }
            
        except Exception as e:
            logger.warning(f"Failed to load extractor from {module_name}: {e}")
            continue
    
    return extractors


def _get_extract_function(module) -> Optional[Callable]:
    """
    Get the extract function from a module.
    
    Looks for either extract_messages() or extract_messages_from_file()
    in the module and returns the first found.
    
    Args:
        module: The imported module
        
    Returns:
        The extract function, or None if not found
    """
    # Try extract_messages first (most common)
    if hasattr(module, 'extract_messages'):
        func = getattr(module, 'extract_messages')
        if callable(func):
            return func
    
    # Try extract_messages_from_file (for file-based extractors)
    if hasattr(module, 'extract_messages_from_file'):
        func = getattr(module, 'extract_messages_from_file')
        if callable(func):
            return func
    
    return None


def _extract_metadata(module, format_name: str) -> Dict[str, Any]:
    """
    Extract metadata from a module with defaults.
    
    Looks for explicit METADATA dict, merges with DEFAULT_METADATA,
    and derives additional metadata from module docstring.
    
    Args:
        module: The imported module
        format_name: The format name (for looking up defaults)
        
    Returns:
        Dict with metadata fields
    """
    # Start with defaults if available
    metadata = {}
    if format_name in DEFAULT_METADATA:
        metadata = DEFAULT_METADATA[format_name].to_dict()
    
    # Check for explicit METADATA dict in module (overrides defaults)
    if hasattr(module, 'METADATA'):
        module_meta = getattr(module, 'METADATA', {})
        metadata.update(module_meta)
    
    # Extract description from docstring if not already set
    if module.__doc__ and 'description' not in metadata:
        metadata['description'] = module.__doc__.strip().split('\n')[0]
    
    return metadata
