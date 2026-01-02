"""
Service for watching a folder and importing conversation files.

Handles:
- Scanning folder for .zip and .json files
- Extracting zip files and finding conversations.json
- Importing via ConversationImportService
- Archiving successful imports
- Moving failed imports with error logs
"""

import os
import json
import shutil
import zipfile
import tempfile
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

from db.services.import_service import ConversationImportService
from db.models.import_result import ImportResult

logger = logging.getLogger(__name__)


@dataclass
class WatchFolderResult:
    """Result of a watch folder scan operation."""
    files_processed: int = 0
    files_succeeded: int = 0
    files_failed: int = 0
    conversations_imported: int = 0
    messages: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class WatchFolderService:
    """Service for watching a folder and importing conversation files."""

    def __init__(self):
        """Initialize the watch folder service."""
        self.import_service = ConversationImportService()

    def scan_folder(self, folder_path: str) -> WatchFolderResult:
        """
        Scan a folder for .zip and .json files and process them.

        Args:
            folder_path: Path to the folder to scan

        Returns:
            WatchFolderResult with processing statistics
        """
        result = WatchFolderResult()

        if not folder_path:
            result.errors.append("No watch folder path configured")
            return result

        folder = Path(folder_path)
        if not folder.exists():
            result.errors.append(f"Watch folder does not exist: {folder_path}")
            return result

        if not folder.is_dir():
            result.errors.append(f"Watch folder path is not a directory: {folder_path}")
            return result

        # Create archive and failed subfolders
        archive_folder = folder / "archive"
        failed_folder = folder / "failed"

        archive_folder.mkdir(exist_ok=True)
        failed_folder.mkdir(exist_ok=True)

        # Find processable files (exclude archive and failed folders)
        files_to_process = []
        for item in folder.iterdir():
            if item.is_file():
                if item.suffix.lower() == '.zip':
                    files_to_process.append(item)
                elif item.suffix.lower() == '.json':
                    files_to_process.append(item)

        if not files_to_process:
            logger.debug(f"No files to process in {folder_path}")
            return result

        logger.info(f"Found {len(files_to_process)} files to process in {folder_path}")
        result.messages.append(f"Found {len(files_to_process)} files to process")

        # Process each file
        for file_path in files_to_process:
            result.files_processed += 1

            try:
                if file_path.suffix.lower() == '.zip':
                    import_result = self.process_zip_file(str(file_path))
                else:
                    import_result = self.process_json_file(str(file_path))

                if import_result.imported_count > 0 or import_result.skipped_duplicates > 0:
                    # Success - archive the file
                    self._archive_file(file_path, archive_folder)
                    result.files_succeeded += 1
                    result.conversations_imported += import_result.imported_count
                    result.messages.append(
                        f"Imported {import_result.imported_count} conversations from {file_path.name}"
                    )
                    logger.info(f"Successfully processed {file_path.name}")
                else:
                    # No conversations found - treat as failure
                    error_msg = "No conversations found in file"
                    self._move_to_failed(file_path, failed_folder, error_msg)
                    result.files_failed += 1
                    result.errors.append(f"{file_path.name}: {error_msg}")

            except Exception as e:
                error_msg = str(e)
                self._move_to_failed(file_path, failed_folder, error_msg)
                result.files_failed += 1
                result.errors.append(f"{file_path.name}: {error_msg}")
                logger.error(f"Failed to process {file_path.name}: {error_msg}")

        # Log summary
        summary = (
            f"Processed {result.files_processed} files: "
            f"{result.files_succeeded} succeeded, {result.files_failed} failed, "
            f"{result.conversations_imported} conversations imported"
        )
        result.messages.append(summary)
        logger.info(summary)

        return result

    def process_zip_file(self, zip_path: str) -> ImportResult:
        """
        Process a zip file by extracting and looking for conversations.json.

        Args:
            zip_path: Path to the zip file

        Returns:
            ImportResult from the import operation

        Raises:
            ValueError: If no conversations.json found or import fails
        """
        logger.info(f"Processing zip file: {zip_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Extract zip
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile:
                raise ValueError(f"Invalid or corrupted zip file: {zip_path}")

            # Look for conversations.json (could be at root or in a subfolder)
            conversations_json_path = self._find_conversations_json(temp_dir)

            if not conversations_json_path:
                raise ValueError("No conversations.json found in zip file")

            # Read and parse the JSON
            try:
                with open(conversations_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in conversations.json: {e}")

            # Import using the existing import service
            return self.import_service.import_json_data(data)

    def process_json_file(self, json_path: str) -> ImportResult:
        """
        Process a JSON file directly.

        Args:
            json_path: Path to the JSON file

        Returns:
            ImportResult from the import operation

        Raises:
            ValueError: If JSON is invalid or import fails
        """
        logger.info(f"Processing JSON file: {json_path}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")

        return self.import_service.import_json_data(data)

    def _find_conversations_json(self, directory: str) -> Optional[str]:
        """
        Find conversations.json in a directory (including subdirectories).

        Args:
            directory: Directory to search

        Returns:
            Path to conversations.json or None if not found
        """
        # First check root level
        root_path = os.path.join(directory, 'conversations.json')
        if os.path.exists(root_path):
            return root_path

        # Check one level of subdirectories (common in exports)
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                nested_path = os.path.join(item_path, 'conversations.json')
                if os.path.exists(nested_path):
                    return nested_path

        return None

    def _archive_file(self, file_path: Path, archive_folder: Path) -> None:
        """
        Move a successfully processed file to the archive folder.

        Args:
            file_path: Path to the file to archive
            archive_folder: Path to the archive folder
        """
        # Add timestamp to avoid conflicts
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        dest_path = archive_folder / new_name

        shutil.move(str(file_path), str(dest_path))
        logger.info(f"Archived {file_path.name} to {dest_path}")

    def _move_to_failed(self, file_path: Path, failed_folder: Path, error: str) -> None:
        """
        Move a failed file to the failed folder and create an error log.

        Args:
            file_path: Path to the failed file
            failed_folder: Path to the failed folder
            error: Error message to log
        """
        # Add timestamp to avoid conflicts
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        dest_path = failed_folder / new_name

        # Move the file
        shutil.move(str(file_path), str(dest_path))

        # Create error log file
        error_log_path = failed_folder / f"{file_path.stem}_{timestamp}.error.txt"
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(f"File: {file_path.name}\n")
            f.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"Error: {error}\n")

        logger.info(f"Moved failed file {file_path.name} to {dest_path}")

    def validate_folder(self, folder_path: str) -> tuple[bool, str]:
        """
        Validate that a folder path exists and is writable.

        Args:
            folder_path: Path to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if not folder_path:
            return False, "Folder path is empty"

        folder = Path(folder_path)

        if not folder.exists():
            return False, f"Folder does not exist: {folder_path}"

        if not folder.is_dir():
            return False, f"Path is not a directory: {folder_path}"

        # Try to create a test file to verify write access
        test_file = folder / ".watch_folder_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            return False, f"No write permission for folder: {folder_path}"
        except Exception as e:
            return False, f"Cannot write to folder: {e}"

        return True, "Folder is valid and writable"
