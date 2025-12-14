"""
Licensing module for feature gating.

Provides license validation and feature access control.
"""

from db.licensing.license_manager import LicenseManager, get_license_manager

__all__ = ["LicenseManager", "get_license_manager"]
