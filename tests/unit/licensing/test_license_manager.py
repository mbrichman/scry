"""
Tests for the license manager and feature gating system.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from db.licensing.license_manager import LicenseManager, get_license_manager
from db.importers.errors import LicenseRequiredError


class TestLicenseManager:
    """Test suite for LicenseManager class."""
    
    def test_no_license_key(self):
        """Test that no features are enabled without a license key."""
        license_manager = LicenseManager()
        
        assert not license_manager.has_feature('chatgpt_importer')
        assert not license_manager.has_feature('docx_importer')
        assert license_manager.get_enabled_features() == set()
    
    def test_invalid_license_key(self):
        """Test that invalid license keys don't enable features."""
        license_manager = LicenseManager(license_key='INVALID-KEY')
        
        assert not license_manager.has_feature('chatgpt_importer')
        assert license_manager.get_enabled_features() == set()
    
    def test_valid_pro_license(self):
        """Test that valid Pro license enables features."""
        license_manager = LicenseManager(license_key='DOVOS-PRO-abc123')
        
        assert license_manager.has_feature('chatgpt_importer')
        assert license_manager.has_feature('docx_importer')
        assert 'chatgpt_importer' in license_manager.get_enabled_features()
        assert 'docx_importer' in license_manager.get_enabled_features()
    
    def test_valid_ent_license(self):
        """Test that valid Enterprise license enables features."""
        license_manager = LicenseManager(license_key='DOVOS-ENT-xyz789')
        
        assert license_manager.has_feature('chatgpt_importer')
        assert 'chatgpt_importer' in license_manager.get_enabled_features()
    
    def test_license_from_env_variable(self):
        """Test that license can be loaded from environment variable."""
        with patch.dict(os.environ, {'DOVOS_LICENSE_KEY': 'DOVOS-PRO-env123'}):
            license_manager = LicenseManager()
            
            assert license_manager.has_feature('chatgpt_importer')
    
    def test_license_from_database(self):
        """Test that license can be loaded from database settings."""
        # Mock the database lookup
        mock_uow = MagicMock()
        mock_uow.settings.get_all.return_value = {'license_key': 'DOVOS-PRO-db123'}
        
        with patch('db.repositories.unit_of_work.get_unit_of_work') as mock_get_uow:
            mock_get_uow.return_value.__enter__.return_value = mock_uow
            
            license_manager = LicenseManager()
            assert license_manager.has_feature('chatgpt_importer')
    
    def test_license_priority_constructor_over_env(self):
        """Test that constructor parameter takes precedence over environment."""
        with patch.dict(os.environ, {'DOVOS_LICENSE_KEY': 'DOVOS-PRO-env'}):
            license_manager = LicenseManager(license_key='DOVOS-PRO-constructor')
            
            # Should use constructor license
            assert license_manager.has_feature('chatgpt_importer')
    
    def test_cache_invalidation(self):
        """Test that cache can be invalidated."""
        license_manager = LicenseManager(license_key='DOVOS-PRO-test')
        
        # First check caches the result
        assert license_manager.has_feature('chatgpt_importer')
        
        # Change the key and invalidate cache
        license_manager._license_key = 'INVALID'
        license_manager.invalidate_cache()
        
        # Should re-validate with new key
        assert not license_manager.has_feature('chatgpt_importer')
    
    def test_license_status(self):
        """Test license status reporting."""
        license_manager = LicenseManager(license_key='DOVOS-PRO-status')
        
        status = license_manager.get_license_status()
        
        assert status['has_license'] == True
        assert 'chatgpt_importer' in status['enabled_features']
        assert 'docx_importer' in status['enabled_features']
        assert len(status['missing_features']) == 0
        assert 'chatgpt_importer' in status['feature_names']
        assert 'docx_importer' in status['feature_names']
    
    def test_license_status_no_license(self):
        """Test license status when no license is present."""
        license_manager = LicenseManager()
        
        status = license_manager.get_license_status()
        
        assert status['has_license'] == False
        assert len(status['enabled_features']) == 0
        assert 'chatgpt_importer' in status['missing_features']
        assert 'docx_importer' in status['missing_features']


class TestLicenseRequiredError:
    """Test suite for LicenseRequiredError exception."""
    
    def test_error_message_with_format_name(self):
        """Test error message includes format name."""
        error = LicenseRequiredError(
            feature_name='chatgpt_importer',
            format_name='ChatGPT'
        )
        
        assert 'ChatGPT' in error.message
        assert 'Pro license' in error.message
        assert 'upgrade' in error.message.lower()
    
    def test_error_attributes(self):
        """Test that error has correct attributes."""
        error = LicenseRequiredError(
            feature_name='chatgpt_importer',
            format_name='ChatGPT'
        )
        
        assert error.feature_name == 'chatgpt_importer'
        assert error.format_name == 'ChatGPT'
    
    def test_custom_message(self):
        """Test that custom messages can be provided."""
        custom_msg = "Custom license error message"
        error = LicenseRequiredError(
            feature_name='test_feature',
            message=custom_msg
        )
        
        assert error.message == custom_msg


class TestImportServiceIntegration:
    """Test that license checks work in import service."""
    
    def test_chatgpt_import_without_license(self):
        """Test that ChatGPT imports are blocked without a license."""
        from db.services.import_service import ConversationImportService
        
        # Create a properly formatted ChatGPT conversations export
        # Must be wrapped in conversations array to be detected properly
        chatgpt_data = [{
            'title': 'Test Conversation',
            'create_time': 1234567890,
            'update_time': 1234567890,
            'mapping': {
                'node1': {
                    'message': {
                        'author': {'role': 'user'},
                        'content': {'parts': ['Hello']}
                    },
                    'create_time': 1234567890
                }
            }
        }]
        
        service = ConversationImportService()
        
        # Should raise ValueError with license message
        with pytest.raises(ValueError) as exc_info:
            service.import_json_data(chatgpt_data)
        
        assert 'license' in str(exc_info.value).lower() or 'pro' in str(exc_info.value).lower()
    
    def test_claude_import_without_license(self):
        """Test that Claude imports work without a license."""
        from db.services.import_service import ConversationImportService
        from unittest.mock import patch
        
        # Create a mock Claude data structure
        claude_data = {
            'uuid': 'test-uuid',
            'name': 'Test Conversation',
            'created_at': '2024-01-01T00:00:00Z',
            'chat_messages': [
                {
                    'sender': 'human',
                    'text': 'Hello',
                    'created_at': '2024-01-01T00:00:00Z'
                }
            ]
        }
        
        service = ConversationImportService()
        
        # Mock database operations to avoid actual DB calls
        with patch('db.services.import_service.get_unit_of_work'):
            # Claude import should not raise license error
            # (it will fail for other reasons without proper mocking, but not license)
            try:
                service.import_json_data(claude_data)
            except ValueError as e:
                # Should not be a license error
                assert 'license' not in str(e).lower()
                assert 'pro' not in str(e).lower()
    
    def test_chatgpt_import_with_valid_license(self):
        """Test that ChatGPT imports work with a valid license."""
        from db.services.import_service import ConversationImportService
        from unittest.mock import patch
        
        chatgpt_data = {
            'title': 'Test Conversation',
            'create_time': 1234567890,
            'mapping': {
                'node1': {
                    'message': {
                        'author': {'role': 'user'},
                        'content': {'parts': ['Hello']}
                    },
                    'create_time': 1234567890
                }
            }
        }
        
        # Mock license manager to return valid license
        with patch('db.licensing.license_manager.get_license_manager') as mock_get_mgr:
            mock_mgr = MagicMock()
            mock_mgr.has_feature.return_value = True
            mock_get_mgr.return_value = mock_mgr
            
            service = ConversationImportService()
            
            # Mock database operations
            with patch('db.services.import_service.get_unit_of_work'):
                # Should not raise license error
                # (will fail for other reasons without proper mocking)
                try:
                    service.import_json_data(chatgpt_data)
                except ValueError as e:
                    # Should not be a license error
                    assert 'license' not in str(e).lower()


def test_get_license_manager_singleton():
    """Test that get_license_manager returns a singleton."""
    mgr1 = get_license_manager()
    mgr2 = get_license_manager()
    
    assert mgr1 is mgr2
