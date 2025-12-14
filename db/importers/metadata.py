"""
Metadata schema and utilities for extractors.

Defines the structure and defaults for extractor metadata.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class ExtractorMetadata:
    """Metadata for a message extractor."""
    
    # Basic information
    name: str  # Human-readable name (e.g., "ChatGPT")
    version: str  # Semantic version (e.g., "1.0.0")
    description: str  # What this extractor handles
    author: str  # Maintainer name
    
    # Format information
    supported_extensions: List[str] = field(default_factory=lambda: [])  # e.g., [".json"]
    
    # Capabilities
    capabilities: Dict[str, Any] = field(default_factory=dict)  # Feature flags
    
    # Format specification
    format_spec: Dict[str, Any] = field(default_factory=dict)  # Expected input format
    
    # Breaking changes history
    breaking_changes: List[Dict[str, str]] = field(default_factory=list)  # Version history
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'supported_extensions': self.supported_extensions,
            'capabilities': self.capabilities,
            'format_spec': self.format_spec,
            'breaking_changes': self.breaking_changes,
        }


# Default metadata for built-in extractors
DEFAULT_METADATA: Dict[str, ExtractorMetadata] = {
    # ChatGPT and DOCX importers are premium features
    # Available with Dovos Pro or Enterprise license
    # Contact us for licensing information
    'claude': ExtractorMetadata(
        name='Claude',
        version='1.0.0',
        description='Claude format message extractor. Extracts messages from Claude\'s chat_messages list format.',
        author='DovOS Contributors',
        supported_extensions=['.json'],
        capabilities={'auto_detect': True, 'streaming': False},
        format_spec={
            'description': 'Claude JSON export format',
            'input_type': 'list',
            'structure': 'List of chat_messages where each message has sender and text',
            'required_fields': ['sender', 'text'],
            'sender_mapping': 'human -> user, others -> assistant',
        },
        breaking_changes=[],
    ),
    'openwebui': ExtractorMetadata(
        name='OpenWebUI',
        version='1.0.0',
        description='OpenWebUI format message extractor. Extracts and flattens messages from OpenWebUI\'s tree-structured dict format.',
        author='DovOS Contributors',
        supported_extensions=['.json'],
        capabilities={'auto_detect': True, 'streaming': False, 'tree_flattening': True},
        format_spec={
            'description': 'OpenWebUI JSON export format',
            'input_type': 'dict',
            'structure': 'Dict with message_id -> message_data mapping, messages have role, content, timestamp',
            'required_fields': ['role', 'content'],
            'timestamp_handling': 'Handles nanoseconds, milliseconds, and seconds',
        },
        breaking_changes=[],
    ),
}
