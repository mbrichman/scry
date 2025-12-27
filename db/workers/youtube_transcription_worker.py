"""
Background worker for processing YouTube transcription jobs.

This worker:
- Fetches transcripts from YouTube videos using youtube-transcript-api
- Uses FOR UPDATE SKIP LOCKED for concurrent processing
- Implements exponential backoff retry logic
- Handles job failures gracefully
- Provides comprehensive logging and metrics
"""

import os
import sys
import time
import signal
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone
import threading
from contextlib import contextmanager

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from db.repositories.unit_of_work import get_unit_of_work
from db.models.models import Job, Message

logger = logging.getLogger(__name__)


class YouTubeTranscriptionFetcher:
    """Handles YouTube transcript fetching using youtube-transcript-api."""

    def __init__(self):
        self.available = False
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            self.api = YouTubeTranscriptApi
            self.available = True
            logger.info("✅ YouTube Transcript API loaded successfully")
        except ImportError:
            logger.warning("youtube-transcript-api not installed. Transcription features will be disabled.")
            logger.warning("Install with: pip install youtube-transcript-api")

    def fetch_transcript(self, video_id: str, languages: List[str] = None) -> Dict:
        """
        Fetch transcript for a YouTube video.

        Args:
            video_id: YouTube video ID
            languages: List of preferred language codes (default: ['en'])

        Returns:
            Dict with:
            - transcript: Full transcript text
            - language: Language code of transcript
            - is_generated: Whether transcript was auto-generated
            - segments: List of transcript segments with timestamps
        """
        if not self.available:
            raise RuntimeError("youtube-transcript-api not installed")

        if languages is None:
            languages = ['en']

        try:
            # Try to fetch transcript in preferred languages
            transcript_list = self.api.list_transcripts(video_id)

            # Try manual transcripts first
            try:
                transcript = transcript_list.find_transcript(languages)
                is_generated = False
            except:
                # Fall back to generated transcripts
                transcript = transcript_list.find_generated_transcript(languages)
                is_generated = True

            # Fetch the actual transcript data
            segments = transcript.fetch()

            # Combine all text into a single transcript
            full_text = " ".join(segment['text'] for segment in segments)

            return {
                'transcript': full_text,
                'language': transcript.language_code,
                'is_generated': is_generated,
                'segments': segments,
                'duration': segments[-1]['start'] + segments[-1]['duration'] if segments else 0
            }

        except Exception as e:
            logger.error(f"Failed to fetch transcript for video {video_id}: {e}")
            raise


class YouTubeTranscriptionWorker:
    """
    Background worker that processes YouTube transcription jobs from PostgreSQL queue.
    """

    def __init__(self,
                 worker_id: str = None,
                 max_jobs_per_batch: int = 5,
                 poll_interval_seconds: int = 2,
                 max_retries: int = 3):
        self.worker_id = worker_id or f"yt-worker-{os.getpid()}-{threading.get_ident()}"
        self.max_jobs_per_batch = max_jobs_per_batch
        self.poll_interval_seconds = poll_interval_seconds
        self.max_retries = max_retries
        self.running = False
        self.transcription_fetcher = YouTubeTranscriptionFetcher()

        # Stats
        self.stats = {
            'jobs_processed': 0,
            'jobs_successful': 0,
            'jobs_failed': 0,
            'start_time': None,
            'last_job_time': None
        }

        # Signal handling
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown on SIGINT/SIGTERM."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def start(self):
        """Start the worker loop."""
        if not self.transcription_fetcher.available:
            logger.error("YouTube Transcript API not available. Worker cannot start.")
            logger.error("Install with: pip install youtube-transcript-api")
            return

        self.running = True
        self.stats['start_time'] = datetime.now(timezone.utc)

        logger.info(f"🚀 YouTube transcription worker {self.worker_id} started")
        logger.info(f"Configuration: max_jobs_per_batch={self.max_jobs_per_batch}, "
                   f"poll_interval={self.poll_interval_seconds}s")

        while self.running:
            try:
                jobs_processed = self._process_batch()

                if jobs_processed == 0:
                    # No jobs found, wait before polling again
                    time.sleep(self.poll_interval_seconds)
                else:
                    # Jobs found, process immediately
                    continue

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}", exc_info=True)
                time.sleep(self.poll_interval_seconds)

        # Print final stats
        self._print_stats()
        logger.info(f"👋 YouTube transcription worker {self.worker_id} stopped")

    def _process_batch(self) -> int:
        """
        Process a batch of YouTube transcription jobs.

        Returns:
            Number of jobs processed
        """
        jobs_processed = 0

        with get_unit_of_work() as uow:
            # Fetch jobs using FOR UPDATE SKIP LOCKED
            jobs = uow.jobs.get_pending_jobs(
                kind='youtube_transcription',
                limit=self.max_jobs_per_batch
            )

            if not jobs:
                return 0

            for job in jobs:
                try:
                    self._process_job(job, uow)
                    jobs_processed += 1
                    self.stats['jobs_successful'] += 1
                except Exception as e:
                    logger.error(f"Failed to process job {job.id}: {e}", exc_info=True)
                    self._handle_job_failure(job, uow, str(e))
                    self.stats['jobs_failed'] += 1

                self.stats['jobs_processed'] += 1
                self.stats['last_job_time'] = datetime.now(timezone.utc)

            uow.commit()

        return jobs_processed

    def _process_job(self, job: Job, uow):
        """
        Process a single YouTube transcription job.

        Args:
            job: The job to process
            uow: Unit of work for database operations
        """
        payload = job.payload
        message_id = payload.get('message_id')
        video_id = payload.get('video_id')

        if not message_id or not video_id:
            raise ValueError(f"Invalid job payload: missing message_id or video_id")

        logger.info(f"Processing transcription for video {video_id} (message {message_id})")

        # Fetch the message
        message = uow.messages.get_by_id(message_id)
        if not message:
            raise ValueError(f"Message {message_id} not found")

        # Fetch transcript
        try:
            transcript_data = self.transcription_fetcher.fetch_transcript(video_id)
        except Exception as e:
            # Update metadata to mark transcription as failed
            metadata = message.message_metadata or {}
            metadata['transcript_status'] = 'failed'
            metadata['transcript_error'] = str(e)
            uow.messages.update_metadata(message_id, metadata)
            raise

        # Update message metadata with transcript
        metadata = message.message_metadata or {}
        metadata['transcript'] = transcript_data['transcript']
        metadata['transcript_language'] = transcript_data['language']
        metadata['transcript_is_generated'] = transcript_data['is_generated']
        metadata['transcript_status'] = 'completed'
        metadata['video_duration'] = transcript_data.get('duration', 0)

        uow.messages.update_metadata(message_id, metadata)

        # Mark job as completed
        uow.jobs.mark_complete(job.id)

        logger.info(f"✅ Completed transcription for video {video_id} "
                   f"({len(transcript_data['transcript'])} chars, {transcript_data['language']})")

    def _handle_job_failure(self, job: Job, uow, error_message: str):
        """
        Handle a failed job with retry logic.

        Args:
            job: The failed job
            uow: Unit of work
            error_message: Error message from the failure
        """
        job.attempts += 1

        if job.attempts >= self.max_retries:
            logger.error(f"Job {job.id} failed after {job.attempts} attempts, marking as failed")
            uow.jobs.mark_failed(job.id, error_message)
        else:
            # Exponential backoff: 2^attempts minutes
            backoff_minutes = 2 ** job.attempts
            retry_time = datetime.now(timezone.utc) + timedelta(minutes=backoff_minutes)

            logger.warning(f"Job {job.id} failed (attempt {job.attempts}/{self.max_retries}), "
                          f"retrying at {retry_time}")

            # Update job for retry
            uow.jobs.schedule_retry(job.id, retry_time, job.attempts)

    def _print_stats(self):
        """Print worker statistics."""
        if self.stats['start_time']:
            runtime = datetime.now(timezone.utc) - self.stats['start_time']
            logger.info(f"📊 Worker Statistics:")
            logger.info(f"   Runtime: {runtime}")
            logger.info(f"   Jobs processed: {self.stats['jobs_processed']}")
            logger.info(f"   Jobs successful: {self.stats['jobs_successful']}")
            logger.info(f"   Jobs failed: {self.stats['jobs_failed']}")


def main():
    """Main entry point for the YouTube transcription worker."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    worker = YouTubeTranscriptionWorker(
        max_jobs_per_batch=int(os.getenv('YOUTUBE_WORKER_BATCH_SIZE', '5')),
        poll_interval_seconds=int(os.getenv('YOUTUBE_WORKER_POLL_INTERVAL', '2')),
        max_retries=int(os.getenv('YOUTUBE_WORKER_MAX_RETRIES', '3'))
    )

    worker.start()


if __name__ == '__main__':
    main()
