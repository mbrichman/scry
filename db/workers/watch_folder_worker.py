"""
Background worker for watching a folder and importing conversation files.

This worker:
- Polls a configured folder for .zip and .json files
- Extracts and imports conversations using WatchFolderService
- Archives successful imports to ./archive subfolder
- Moves failed imports to ./failed subfolder with error logs
- Provides heartbeat mechanism for health monitoring
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime, timezone

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from db.repositories.unit_of_work import get_unit_of_work
from db.services.watch_folder_service import WatchFolderService

logger = logging.getLogger(__name__)


class WatchFolderWorker:
    """
    Background worker that watches a folder for conversation files to import.
    """

    def __init__(self, poll_interval_seconds: int = 30):
        """
        Initialize the watch folder worker.

        Args:
            poll_interval_seconds: How often to scan the folder (default 30s)
        """
        self.poll_interval_seconds = poll_interval_seconds
        self.running = False
        self.watch_folder_service = WatchFolderService()

        # Stats
        self.stats = {
            'scans_completed': 0,
            'files_processed': 0,
            'conversations_imported': 0,
            'errors': 0,
            'start_time': None,
            'last_scan_time': None
        }

        # Heartbeat tracking
        self.last_heartbeat_time = None
        self.heartbeat_interval = 30  # seconds

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()

    def _update_heartbeat(self):
        """Update heartbeat timestamp in settings table."""
        try:
            with get_unit_of_work() as uow:
                uow.settings.create_or_update(
                    'watch_folder_worker_heartbeat',
                    datetime.now(timezone.utc).isoformat(),
                    category='import'
                )
            self.last_heartbeat_time = datetime.now(timezone.utc)
            logger.debug("Heartbeat updated")
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")

    def _should_update_heartbeat(self) -> bool:
        """Check if heartbeat should be updated."""
        if self.last_heartbeat_time is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self.last_heartbeat_time).total_seconds()
        return elapsed >= self.heartbeat_interval

    def _get_watch_folder_settings(self) -> tuple[str, bool, int]:
        """
        Get watch folder settings from database.

        Returns:
            Tuple of (folder_path, enabled, poll_interval)
        """
        try:
            with get_unit_of_work() as uow:
                folder_path = uow.settings.get_value('watch_folder_path', '')
                enabled = uow.settings.get_value('watch_folder_enabled', 'false').lower() == 'true'
                poll_interval = int(uow.settings.get_value('watch_folder_poll_interval', '30'))
                return folder_path, enabled, poll_interval
        except Exception as e:
            logger.error(f"Failed to get watch folder settings: {e}")
            return '', False, 30

    def _update_last_check(self):
        """Update the last check timestamp in settings."""
        try:
            with get_unit_of_work() as uow:
                uow.settings.create_or_update(
                    'watch_folder_last_check',
                    datetime.now(timezone.utc).isoformat(),
                    category='import'
                )
        except Exception as e:
            logger.error(f"Failed to update last check timestamp: {e}")

    def start(self):
        """Start the worker loop."""
        self.running = True
        self.stats['start_time'] = datetime.now(timezone.utc)

        logger.info("Starting watch folder worker")
        logger.info(f"   Default poll interval: {self.poll_interval_seconds}s")

        # Initial heartbeat
        self._update_heartbeat()

        try:
            while self.running:
                # Update heartbeat if needed
                if self._should_update_heartbeat():
                    self._update_heartbeat()

                # Get current settings
                folder_path, enabled, poll_interval = self._get_watch_folder_settings()

                if enabled and folder_path:
                    self._scan_folder(folder_path)
                elif not enabled:
                    logger.debug("Watch folder is disabled")
                elif not folder_path:
                    logger.debug("No watch folder path configured")

                # Use the configured poll interval
                actual_interval = poll_interval if poll_interval > 0 else self.poll_interval_seconds
                time.sleep(actual_interval)

        except KeyboardInterrupt:
            logger.info("Worker interrupted by user")
        except Exception as e:
            logger.error(f"Worker crashed: {e}")
            raise
        finally:
            self._log_final_stats()

    def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        logger.info("Stopping watch folder worker")

    def _scan_folder(self, folder_path: str):
        """
        Perform a single scan of the watch folder.

        Args:
            folder_path: Path to the folder to scan
        """
        logger.debug(f"Scanning folder: {folder_path}")

        try:
            result = self.watch_folder_service.scan_folder(folder_path)

            self.stats['scans_completed'] += 1
            self.stats['files_processed'] += result.files_processed
            self.stats['conversations_imported'] += result.conversations_imported
            self.stats['errors'] += result.files_failed
            self.stats['last_scan_time'] = datetime.now(timezone.utc)

            # Update last check timestamp
            self._update_last_check()

            if result.files_processed > 0:
                logger.info(
                    f"Scan complete: {result.files_succeeded} succeeded, "
                    f"{result.files_failed} failed, "
                    f"{result.conversations_imported} conversations imported"
                )

        except Exception as e:
            logger.error(f"Folder scan failed: {e}")
            self.stats['errors'] += 1

    def _log_final_stats(self):
        """Log final statistics when worker stops."""
        if self.stats['start_time']:
            runtime = datetime.now(timezone.utc) - self.stats['start_time']
            logger.info(f"Final stats for watch folder worker:")
            logger.info(f"   Runtime: {runtime}")
            logger.info(f"   Scans completed: {self.stats['scans_completed']}")
            logger.info(f"   Files processed: {self.stats['files_processed']}")
            logger.info(f"   Conversations imported: {self.stats['conversations_imported']}")
            logger.info(f"   Errors: {self.stats['errors']}")


def main():
    """Main entry point for running the watch folder worker."""
    import argparse

    parser = argparse.ArgumentParser(description="Watch Folder Import Worker")
    parser.add_argument("--poll-interval", type=int, default=30, help="Poll interval in seconds")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        worker = WatchFolderWorker(poll_interval_seconds=args.poll_interval)
        worker.start()

    except KeyboardInterrupt:
        logger.info("Worker shutdown complete")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        raise


if __name__ == "__main__":
    main()
