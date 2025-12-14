"""
License manager for feature gating and validation.

Manages license keys for premium features like the ChatGPT importer.
License keys can be provided via:
1. Environment variable: DOVOS_LICENSE_KEY
2. Database settings (via settings table)
"""

import os
import logging
from typing import Optional, Set
import hashlib

logger = logging.getLogger(__name__)


class LicenseManager:
    """Manages license validation and feature access control."""
    
    # Features that require a license
    LICENSED_FEATURES = {
        'chatgpt_importer': 'ChatGPT Importer',
        'docx_importer': 'DOCX Importer'
    }
    
    def __init__(self, license_key: Optional[str] = None):
        """Initialize the license manager.
        
        Args:
            license_key: Optional license key. If not provided, will check environment
                        and database settings.
        """
        self._license_key = license_key
        self._validated_features: Optional[Set[str]] = None
    
    def _get_license_key(self) -> Optional[str]:
        """Get license key from multiple sources.
        
        Priority order:
        1. Constructor parameter
        2. Environment variable DOVOS_LICENSE_KEY
        3. Database settings
        
        Returns:
            License key string or None
        """
        # Check constructor parameter
        if self._license_key:
            return self._license_key
        
        # Check environment variable
        env_key = os.getenv('DOVOS_LICENSE_KEY')
        if env_key:
            return env_key
        
        # Check database settings
        try:
            from db.repositories.unit_of_work import get_unit_of_work
            with get_unit_of_work() as uow:
                settings = uow.settings.get_all()
                return settings.get('license_key')
        except Exception as e:
            logger.debug(f"Could not fetch license from database: {e}")
            return None
    
    def _validate_license_key(self, license_key: str) -> Set[str]:
        """Validate a license key and return enabled features.
        
        For MVP, we use a simple validation scheme:
        - Valid keys are SHA256 hashes
        - Different hash prefixes unlock different features
        
        Args:
            license_key: License key to validate
            
        Returns:
            Set of enabled feature names
        """
        if not license_key:
            return set()
        
        # For MVP: simple validation
        # Pro license format: "DOVOS-PRO-{hash}"
        # Enterprise license format: "DOVOS-ENT-{hash}"
        
        enabled_features = set()
        
        if license_key.startswith('DOVOS-PRO-') or license_key.startswith('DOVOS-ENT-'):
            # Valid license format - enable premium importers
            enabled_features.add('chatgpt_importer')
            enabled_features.add('docx_importer')
        
        return enabled_features
    
    def has_feature(self, feature_name: str) -> bool:
        """Check if a feature is available with current license.
        
        Args:
            feature_name: Name of the feature to check (e.g., 'chatgpt_importer')
            
        Returns:
            True if feature is available, False otherwise
        """
        # Cache validation result
        if self._validated_features is None:
            license_key = self._get_license_key()
            if license_key:
                self._validated_features = self._validate_license_key(license_key)
            else:
                self._validated_features = set()
        
        return feature_name in self._validated_features
    
    def get_enabled_features(self) -> Set[str]:
        """Get all enabled features for current license.
        
        Returns:
            Set of enabled feature names
        """
        if self._validated_features is None:
            license_key = self._get_license_key()
            if license_key:
                self._validated_features = self._validate_license_key(license_key)
            else:
                self._validated_features = set()
        
        return self._validated_features.copy()
    
    def get_license_status(self) -> dict:
        """Get current license status information.
        
        Returns:
            Dict with license status:
            - has_license: bool
            - enabled_features: list of feature names
            - missing_features: list of feature names
        """
        enabled = self.get_enabled_features()
        all_features = set(self.LICENSED_FEATURES.keys())
        missing = all_features - enabled
        
        return {
            'has_license': bool(self._get_license_key()),
            'enabled_features': list(enabled),
            'missing_features': list(missing),
            'feature_names': {
                name: display_name 
                for name, display_name in self.LICENSED_FEATURES.items()
            }
        }
    
    def invalidate_cache(self):
        """Invalidate the cached validation result.
        
        Call this after updating the license key in settings.
        """
        self._validated_features = None


# Singleton instance
_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """Get the global license manager instance.
    
    Returns:
        LicenseManager singleton instance
    """
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager
