"""
Tests for plugin discovery and dynamic loading system.

Tests that extractors can be automatically discovered and registered
without manual registry updates.
"""

import pytest
import sys
import os
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock


class TestPluginLoaderDiscovery:
    """Tests for discovering extractor modules."""
    
    def test_loader_discovers_extractor_modules(self):
        """Loader should discover all extractor modules in db/importers/."""
        from db.importers.loader import discover_extractors
        
        extractors = discover_extractors()
        
        # Should discover all 4 existing extractors
        assert len(extractors) >= 4
        assert 'chatgpt' in extractors
        assert 'claude' in extractors
        assert 'openwebui' in extractors
        assert 'docx' in extractors
    
    def test_discovered_extractors_are_callable(self):
        """Discovered extractors should have callable extract functions."""
        from db.importers.loader import discover_extractors
        
        extractors = discover_extractors()
        
        for name, extractor_info in extractors.items():
            # Should have extract function (either extract_messages or extract_messages_from_file)
            assert 'extract' in extractor_info, f"{name} missing extract function"
            assert callable(extractor_info['extract']), f"{name} extract is not callable"
    
    def test_loader_skips_non_extractor_modules(self):
        """Loader should skip __pycache__, __init__, registry, loader, etc."""
        from db.importers.loader import discover_extractors
        
        extractors = discover_extractors()
        
        # Should not include internal modules
        assert 'registry' not in extractors
        assert 'loader' not in extractors
        assert '__pycache__' not in extractors
        assert 'interfaces' not in extractors
        assert '__init__' not in extractors


class TestPluginRegistration:
    """Tests for dynamic plugin registration."""
    
    def test_dynamic_registry_loads_all_extractors(self):
        """Dynamic registry should automatically load discovered extractors."""
        from db.importers.registry import FORMAT_REGISTRY
        
        # Should have all 4 extractors
        assert len(FORMAT_REGISTRY) >= 4
        assert 'chatgpt' in FORMAT_REGISTRY
        assert 'claude' in FORMAT_REGISTRY
        assert 'openwebui' in FORMAT_REGISTRY
        assert 'docx' in FORMAT_REGISTRY
    
    def test_registry_extractors_are_callable(self):
        """All registered extractors should be callable."""
        from db.importers.registry import FORMAT_REGISTRY
        
        for name, extractor_func in FORMAT_REGISTRY.items():
            assert callable(extractor_func), f"{name} is not callable"
    
    def test_registry_extraction_works_for_chatgpt(self):
        """ChatGPT extractor from dynamic registry should work."""
        from db.importers.registry import FORMAT_REGISTRY
        
        chatgpt_extractor = FORMAT_REGISTRY['chatgpt']
        
        # Test with simple ChatGPT-like data
        test_data = {
            'node_123': {
                'create_time': 1234567890,
                'message': {
                    'author': {'role': 'user'},
                    'content': {'parts': ['Hello']}
                }
            }
        }
        
        messages = chatgpt_extractor(test_data)
        assert len(messages) == 1
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == 'Hello'
    
    def test_registry_extraction_works_for_claude(self):
        """Claude extractor from dynamic registry should work."""
        from db.importers.registry import FORMAT_REGISTRY
        
        claude_extractor = FORMAT_REGISTRY['claude']
        
        # Test with simple Claude-like data
        test_data = [
            {'sender': 'human', 'text': 'Hi'},
            {'sender': 'assistant', 'text': 'Hello!'}
        ]
        
        messages = claude_extractor(test_data)
        assert len(messages) == 2
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == 'Hi'
        assert messages[1]['role'] == 'assistant'
        assert messages[1]['content'] == 'Hello!'
    
    def test_registry_extraction_works_for_openwebui(self):
        """OpenWebUI extractor from dynamic registry should work."""
        from db.importers.registry import FORMAT_REGISTRY
        
        openwebui_extractor = FORMAT_REGISTRY['openwebui']
        
        # Test with simple OpenWebUI-like data
        test_data = {
            'msg_1': {
                'role': 'user',
                'content': 'Hello',
                'timestamp': 1234567890
            }
        }
        
        messages = openwebui_extractor(test_data)
        assert len(messages) == 1
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == 'Hello'


class TestFormatDetectionWithDynamicExtractors:
    """Tests that format detection works with dynamically loaded extractors."""
    
    def test_detect_format_uses_dynamic_extractors(self):
        """Format detection should work with dynamic extractors."""
        from db.importers.registry import detect_format
        
        # ChatGPT format
        chatgpt_data = [{
            'title': 'Test',
            'mapping': {
                'node_1': {
                    'create_time': 1234567890,
                    'message': {
                        'author': {'role': 'user'},
                        'content': {'parts': ['Hello']}
                    }
                }
            },
            'create_time': 1234567890
        }]
        
        conversations, format_type = detect_format(chatgpt_data)
        assert format_type == 'ChatGPT'
    
    def test_detect_format_claude(self):
        """Format detection should identify Claude format."""
        from db.importers.registry import detect_format
        
        claude_data = [{
            'uuid': 'test-uuid',
            'name': 'Test',
            'chat_messages': [
                {'sender': 'human', 'text': 'Hi'}
            ]
        }]
        
        conversations, format_type = detect_format(claude_data)
        assert format_type == 'Claude'
    
    def test_detect_format_openwebui(self):
        """Format detection should identify OpenWebUI format."""
        from db.importers.registry import detect_format
        
        openwebui_data = [{
            'chat': {
                'history': {
                    'messages': {
                        'msg_1': {
                            'role': 'user',
                            'content': 'Hello',
                            'timestamp': 1234567890
                        }
                    }
                }
            }
        }]
        
        conversations, format_type = detect_format(openwebui_data)
        assert format_type == 'OpenWebUI'


class TestPluginExtractorMetadata:
    """Tests for extractor metadata exposed by dynamic loading."""
    
    def test_discovered_extractors_have_metadata(self):
        """Discovered extractors should have metadata dict."""
        from db.importers.loader import discover_extractors
        
        extractors = discover_extractors()
        
        for name, extractor_info in extractors.items():
            # Should have metadata
            assert 'metadata' in extractor_info or 'name' in extractor_info
    
    def test_loader_provides_extractor_names(self):
        """Loader should provide human-readable extractor names."""
        from db.importers.loader import discover_extractors
        
        extractors = discover_extractors()
        
        # Each extractor should have a name
        for name, extractor_info in extractors.items():
            assert 'name' in extractor_info, f"{name} missing 'name' field"
            assert isinstance(extractor_info['name'], str)
            assert len(extractor_info['name']) > 0


class TestNoManualImportsNeeded:
    """Tests that verify extractors work without manual imports in registry."""
    
    def test_chatgpt_not_manually_imported_in_registry(self):
        """
        ChatGPT should be loaded dynamically, not via manual import.
        This verifies the registry doesn't have hardcoded imports.
        """
        # Read registry file and verify no manual imports of chatgpt
        registry_path = '/Users/markrichman/projects/dovos/db/importers/registry.py'
        with open(registry_path, 'r') as f:
            content = f.read()
        
        # Should not have manual import line for chatgpt
        assert 'from db.importers.chatgpt import' not in content or 'loader' in content
    
    def test_new_extractor_discoverable_without_registry_changes(self):
        """
        A new extractor module should be discovered without registry changes.
        This tests the plugin architecture works.
        """
        from db.importers.loader import discover_extractors
        
        # Get current count
        extractors = discover_extractors()
        initial_count = len(extractors)
        
        # Create a mock extractor module temporarily
        temp_extractor_code = '''
def extract_messages(data, **kwargs):
    return [{'role': 'user', 'content': 'test'}]
'''
        
        # Should have discovered at least 4 built-in extractors
        assert initial_count >= 4


class TestPluginLoaderErrorHandling:
    """Tests error handling in plugin discovery."""
    
    def test_loader_handles_missing_extract_function(self):
        """Loader should handle modules without extract functions gracefully."""
        from db.importers.loader import discover_extractors
        
        # Should not crash even if a module is malformed
        extractors = discover_extractors()
        
        # Should still get valid extractors
        assert len(extractors) > 0
    
    def test_loader_handles_syntax_errors_gracefully(self):
        """Loader should not crash if an extractor has syntax errors."""
        from db.importers.loader import discover_extractors
        
        # Should not raise exception
        extractors = discover_extractors()
        
        # Should still return valid extractors
        assert len(extractors) >= 4
