"""
Data class for structured conversation import operation results.

Provides a consistent interface for import operations to return detailed
information about import success/failure, including counts, format detected,
and any errors or messages that occurred during the import.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ImportResult:
    """Result of a conversation import operation."""
    
    imported_count: int = 0
    """Number of conversations successfully imported."""
    
    skipped_duplicates: int = 0
    """Number of duplicate conversations skipped."""
    
    failed_count: int = 0
    """Number of conversations that failed to import."""
    
    format_detected: str = "Unknown"
    """Detected format (ChatGPT, Claude, OpenWebUI, etc.)."""
    
    messages: List[str] = field(default_factory=list)
    """Informational messages about the import process."""
    
    errors: List[str] = field(default_factory=list)
    """Error messages from the import process."""
    
    def __str__(self) -> str:
        """Return a user-friendly summary of the import result."""
        if self.imported_count == 0 and self.failed_count == 0 and self.skipped_duplicates == 0:
            return "No conversations to import"
        
        parts = []
        if self.imported_count > 0:
            parts.append(f"✅ Imported {self.imported_count} conversations")
        if self.skipped_duplicates > 0:
            parts.append(f"⏭️ Skipped {self.skipped_duplicates} duplicates")
        if self.failed_count > 0:
            parts.append(f"❌ Failed to import {self.failed_count} conversations")
        
        result = " | ".join(parts) if parts else "Import completed"
        
        if self.format_detected != "Unknown":
            result = f"{result} ({self.format_detected} format)"
        
        return result
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "imported_count": self.imported_count,
            "skipped_duplicates": self.skipped_duplicates,
            "failed_count": self.failed_count,
            "format_detected": self.format_detected,
            "messages": self.messages,
            "errors": self.errors,
            "summary": str(self)
        }
