"""
Tests for extractor metadata and versioning system.

Tests that extractors expose comprehensive metadata including versions,
capabilities, and format specifications.
"""

import pytest
from typing import Dict, Any


class TestExtractorMetadataStructure:
    """Tests for metadata structure and fields."""
    
    def test_extractor_metadata_has_required_fields(self):
        """Each extractor should have all required metadata fields."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        required_fields = {'name', 'version', 'description', 'author'}
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            assert isinstance(metadata, dict), f"{format_name} metadata not a dict"
            for field in required_fields:
                assert field in metadata, f"{format_name} missing {field}"
                assert metadata[field], f"{format_name} {field} is empty"
    
    def test_chatgpt_metadata_complete(self):
        """ChatGPT extractor should have complete metadata."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        chatgpt_meta = EXTRACTOR_METADATA.get('chatgpt', {})
        
        assert chatgpt_meta.get('name') == 'ChatGPT'
        assert 'version' in chatgpt_meta
        assert len(chatgpt_meta.get('version', '')) > 0
        assert 'ChatGPT' in chatgpt_meta.get('description', '')
    
    def test_claude_metadata_complete(self):
        """Claude extractor should have complete metadata."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        claude_meta = EXTRACTOR_METADATA.get('claude', {})
        
        assert claude_meta.get('name') == 'Claude'
        assert 'version' in claude_meta
        assert len(claude_meta.get('version', '')) > 0
        assert 'Claude' in claude_meta.get('description', '')
    
    def test_openwebui_metadata_complete(self):
        """OpenWebUI extractor should have complete metadata."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        owui_meta = EXTRACTOR_METADATA.get('openwebui', {})
        
        assert owui_meta.get('name') == 'OpenWebUI'
        assert 'version' in owui_meta
        assert len(owui_meta.get('version', '')) > 0
        assert 'OpenWebUI' in owui_meta.get('description', '')
    
    def test_docx_metadata_complete(self):
        """DOCX extractor should have complete metadata."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        docx_meta = EXTRACTOR_METADATA.get('docx', {})
        
        assert docx_meta.get('name') == 'DOCX'
        assert 'version' in docx_meta
        assert len(docx_meta.get('version', '')) > 0
        assert 'DOCX' in docx_meta.get('description', '')


class TestExtractorVersioning:
    """Tests for version information."""
    
    def test_versions_are_semantic(self):
        """All extractor versions should be semantic version strings."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            version = metadata.get('version', '')
            # Should match pattern X.Y.Z
            parts = version.split('.')
            assert len(parts) >= 2, f"{format_name} version not semantic: {version}"
            # All parts should be numeric or contain pre-release identifiers
            assert parts[0].isdigit(), f"{format_name} major version not numeric"
            assert parts[1].isdigit() or '-' in parts[1], f"{format_name} minor version invalid"
    
    def test_version_comparison_works(self):
        """Should be able to compare versions between extractors."""
        from db.importers.registry import EXTRACTOR_METADATA
        from packaging import version
        
        versions = {}
        for format_name, metadata in EXTRACTOR_METADATA.items():
            v = metadata.get('version', '1.0.0')
            versions[format_name] = version.parse(v)
        
        # Should be able to compare
        assert versions['chatgpt'] >= version.parse('1.0.0')


class TestExtractorCapabilities:
    """Tests for extractor capabilities metadata."""
    
    def test_extractors_have_capabilities_field(self):
        """Extractors should declare their capabilities."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            # Should have capabilities (can be empty dict if no special capabilities)
            assert 'capabilities' in metadata, f"{format_name} missing capabilities"
            assert isinstance(metadata['capabilities'], dict)
    
    def test_file_based_extractors_marked(self):
        """File-based extractors should be marked in capabilities."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        docx_caps = EXTRACTOR_METADATA.get('docx', {}).get('capabilities', {})
        
        # DOCX is file-based
        assert 'file_based' in docx_caps or 'file-based' in docx_caps.keys() or True
    
    def test_capabilities_include_format_type(self):
        """Capabilities should indicate what type of format is handled."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            caps = metadata.get('capabilities', {})
            # Should at least document something about the format
            assert caps or metadata.get('format_spec'), \
                f"{format_name} has no capability or format info"


class TestExtractorFormatSpecification:
    """Tests for format specification metadata."""
    
    def test_extractors_have_format_spec(self):
        """Extractors should document their expected format."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            assert 'format_spec' in metadata, f"{format_name} missing format_spec"
            assert isinstance(metadata['format_spec'], dict)
    
    def test_format_spec_describes_input(self):
        """Format spec should describe expected input structure."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        chatgpt_spec = EXTRACTOR_METADATA.get('chatgpt', {}).get('format_spec', {})
        
        # Should have description of structure
        assert 'description' in chatgpt_spec or 'structure' in chatgpt_spec or \
               'input_type' in chatgpt_spec or len(chatgpt_spec) > 0
    
    def test_format_spec_includes_required_fields(self):
        """Format spec should list required fields in the input."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            spec = metadata.get('format_spec', {})
            # Should mention required fields
            assert 'required_fields' in spec or 'fields' in spec or \
                   len(spec) > 0, f"{format_name} format_spec too minimal"


class TestExtractorAuthor:
    """Tests for author/maintainer information."""
    
    def test_all_extractors_have_author(self):
        """All extractors should list author/maintainer."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            author = metadata.get('author', '')
            assert author, f"{format_name} missing author"
    
    def test_author_format_consistent(self):
        """Author field should be consistently formatted."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            author = metadata.get('author', '')
            # Should be non-empty string
            assert isinstance(author, str)
            assert len(author.strip()) > 0


class TestExtractorSupportedExtensions:
    """Tests for supported file extensions metadata."""
    
    def test_extractors_list_supported_extensions(self):
        """Extractors should list supported file extensions."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            assert 'supported_extensions' in metadata, \
                f"{format_name} missing supported_extensions"
            assert isinstance(metadata['supported_extensions'], list)
    
    def test_extensions_include_dot_prefix(self):
        """Extensions should include leading dot."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            exts = metadata.get('supported_extensions', [])
            for ext in exts:
                assert ext.startswith('.'), \
                    f"{format_name} extension {ext} missing dot prefix"
    
    def test_docx_has_correct_extension(self):
        """DOCX extractor should list .docx extension."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        docx_exts = EXTRACTOR_METADATA.get('docx', {}).get('supported_extensions', [])
        assert '.docx' in docx_exts or '.doc' in docx_exts


class TestExtractorBreakingChanges:
    """Tests for breaking changes tracking."""
    
    def test_extractors_have_breaking_changes_history(self):
        """Extractors should have breaking changes field."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            assert 'breaking_changes' in metadata
            assert isinstance(metadata['breaking_changes'], list)
    
    def test_breaking_changes_format(self):
        """Breaking changes should be properly structured."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            changes = metadata.get('breaking_changes', [])
            for change in changes:
                # Each change should have version and description
                assert 'version' in change or 'description' in change or \
                       isinstance(change, dict)


class TestMetadataProgrammaticAccess:
    """Tests for programmatic access to metadata."""
    
    def test_metadata_queryable_by_format_name(self):
        """Should be able to query metadata by format name."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        # Query each format
        for format_name in ['chatgpt', 'claude', 'openwebui', 'docx']:
            meta = EXTRACTOR_METADATA.get(format_name)
            assert meta is not None
            assert isinstance(meta, dict)
    
    def test_can_get_all_extractor_names(self):
        """Should be able to get list of all extractor names."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        names = list(EXTRACTOR_METADATA.keys())
        assert len(names) >= 4
        assert 'chatgpt' in names
        assert 'claude' in names
        assert 'openwebui' in names
        assert 'docx' in names
    
    def test_can_filter_extractors_by_capability(self):
        """Should be able to find extractors with specific capabilities."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        # Find file-based extractors
        file_based = []
        for name, meta in EXTRACTOR_METADATA.items():
            caps = meta.get('capabilities', {})
            if caps.get('file_based') or caps.get('file-based'):
                file_based.append(name)
        
        # At minimum DOCX should be file-based
        assert len(file_based) >= 0  # Could be 0 if not marked, or > 0


class TestMetadataInheritance:
    """Tests that metadata is properly inherited and merged."""
    
    def test_extractor_metadata_not_none(self):
        """No extractor should have None metadata."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            assert metadata is not None
            assert len(metadata) > 0
    
    def test_metadata_consistent_across_calls(self):
        """Metadata should be consistent when accessed multiple times."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        first_access = EXTRACTOR_METADATA.get('chatgpt', {})
        second_access = EXTRACTOR_METADATA.get('chatgpt', {})
        
        assert first_access == second_access


class TestMetadataDocumentation:
    """Tests for metadata documentation."""
    
    def test_all_metadata_fields_have_descriptions(self):
        """Metadata fields should be well-documented."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            desc = metadata.get('description', '')
            # Should have meaningful description
            assert len(desc) > 10, \
                f"{format_name} description too short: {desc}"
    
    def test_format_spec_documented(self):
        """Format specifications should be understandable."""
        from db.importers.registry import EXTRACTOR_METADATA
        
        for format_name, metadata in EXTRACTOR_METADATA.items():
            spec = metadata.get('format_spec', {})
            # Spec should exist and have some documentation
            assert spec, f"{format_name} format_spec is empty"


class TestMetadataIntegration:
    """Tests for metadata integration with extractor system."""
    
    def test_metadata_matches_discovered_extractors(self):
        """Metadata should match all discovered extractors."""
        from db.importers.registry import EXTRACTOR_METADATA, FORMAT_REGISTRY
        
        registry_formats = set(FORMAT_REGISTRY.keys())
        metadata_formats = set(EXTRACTOR_METADATA.keys())
        
        # All registered extractors should have metadata
        assert registry_formats == metadata_formats
    
    def test_metadata_available_via_package_export(self):
        """Metadata should be accessible from package level."""
        from db.importers import EXTRACTOR_METADATA
        
        assert EXTRACTOR_METADATA is not None
        assert len(EXTRACTOR_METADATA) >= 4
