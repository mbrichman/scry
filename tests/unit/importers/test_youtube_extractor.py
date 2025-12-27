"""
Unit tests for YouTube watch history message extraction.

Tests the extraction of messages from YouTube watch history exported via Google Takeout.
"""

import pytest
from typing import Dict, List, Any


class TestYouTubeExtractor:
    """Test suite for YouTube watch history message extraction."""

    def test_extract_basic_watch_events(self):
        """Test extraction of basic watch events."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Building a RAG System from Scratch",
                "titleUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "time": "2024-01-15T14:30:00.000Z",
                "subtitles": [
                    {
                        "name": "Tech Education Channel",
                        "url": "https://www.youtube.com/channel/UC1234567890"
                    }
                ]
            },
            {
                "title": "Introduction to Vector Databases",
                "titleUrl": "https://www.youtube.com/watch?v=abc123xyz",
                "time": "2024-01-16T10:15:00.000Z",
                "subtitles": [
                    {
                        "name": "Database Learning",
                        "url": "https://www.youtube.com/channel/UC9876543210"
                    }
                ]
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 2
        assert all(msg["role"] == "user" for msg in messages)
        assert "Building a RAG System from Scratch" in messages[0]["content"]
        assert "Introduction to Vector Databases" in messages[1]["content"]

    def test_extract_preserves_timestamps(self):
        """Test that timestamps are preserved and converted correctly."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Test Video",
                "titleUrl": "https://www.youtube.com/watch?v=test123",
                "time": "2024-01-15T14:30:00.000Z"
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 1
        assert "created_at" in messages[0]
        # Timestamp should be a float (Unix timestamp)
        assert isinstance(messages[0]["created_at"], float)
        assert messages[0]["created_at"] > 0

    def test_extract_video_id_from_url(self):
        """Test that video ID is extracted from various YouTube URL formats."""
        from db.importers.youtube import extract_video_id

        # Standard watch URL
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

        # Short URL
        assert extract_video_id("https://youtu.be/abc123xyz") == "abc123xyz"

        # Embed URL
        assert extract_video_id("https://www.youtube.com/embed/test123") == "test123"

        # URL with additional parameters
        assert extract_video_id("https://www.youtube.com/watch?v=vid123&t=30s") == "vid123"

        # Invalid URL
        assert extract_video_id("https://example.com") == ""
        assert extract_video_id("") == ""

    def test_extract_includes_channel_info(self):
        """Test that channel information is included in metadata."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Test Video",
                "titleUrl": "https://www.youtube.com/watch?v=test123",
                "time": "2024-01-15T14:30:00.000Z",
                "subtitles": [
                    {
                        "name": "Channel Name",
                        "url": "https://www.youtube.com/channel/UC123456"
                    }
                ]
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 1
        metadata = messages[0]["metadata"]
        assert metadata["channel_name"] == "Channel Name"
        assert metadata["channel_url"] == "https://www.youtube.com/channel/UC123456"
        assert "by Channel Name" in messages[0]["content"]

    def test_extract_handles_missing_channel_info(self):
        """Test handling of watch events without channel information."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Test Video",
                "titleUrl": "https://www.youtube.com/watch?v=test123",
                "time": "2024-01-15T14:30:00.000Z"
                # No subtitles field
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 1
        metadata = messages[0]["metadata"]
        assert "channel_name" not in metadata
        assert messages[0]["content"] == "Watched: Test Video"

    def test_extract_includes_video_metadata(self):
        """Test that video metadata is properly stored."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Test Video",
                "titleUrl": "https://www.youtube.com/watch?v=test123",
                "time": "2024-01-15T14:30:00.000Z"
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 1
        metadata = messages[0]["metadata"]
        assert metadata["video_id"] == "test123"
        assert metadata["video_url"] == "https://www.youtube.com/watch?v=test123"
        assert metadata["transcript_status"] == "pending"
        assert metadata["transcript"] is None
        assert metadata["summary"] is None

    def test_extract_skips_invalid_entries(self):
        """Test that invalid entries are skipped."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Valid Video",
                "titleUrl": "https://www.youtube.com/watch?v=valid123",
                "time": "2024-01-15T14:30:00.000Z"
            },
            {
                # Missing title
                "titleUrl": "https://www.youtube.com/watch?v=missing_title",
                "time": "2024-01-15T14:30:00.000Z"
            },
            {
                "title": "Missing URL",
                # Missing titleUrl
                "time": "2024-01-15T14:30:00.000Z"
            },
            {
                "title": "Invalid URL",
                "titleUrl": "https://example.com/not_youtube",
                "time": "2024-01-15T14:30:00.000Z"
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 1
        assert "Valid Video" in messages[0]["content"]

    def test_extract_orders_by_timestamp(self):
        """Test that messages are ordered by timestamp (oldest first)."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Third Video",
                "titleUrl": "https://www.youtube.com/watch?v=third",
                "time": "2024-01-17T14:30:00.000Z"
            },
            {
                "title": "First Video",
                "titleUrl": "https://www.youtube.com/watch?v=first",
                "time": "2024-01-15T14:30:00.000Z"
            },
            {
                "title": "Second Video",
                "titleUrl": "https://www.youtube.com/watch?v=second",
                "time": "2024-01-16T14:30:00.000Z"
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 3
        assert "First Video" in messages[0]["content"]
        assert "Second Video" in messages[1]["content"]
        assert "Third Video" in messages[2]["content"]

    def test_extract_handles_empty_list(self):
        """Test extraction from empty watch history."""
        from db.importers.youtube import extract_messages

        messages = extract_messages([])
        assert messages == []

    def test_extract_handles_invalid_input(self):
        """Test handling of invalid input types."""
        from db.importers.youtube import extract_messages

        # Not a list
        messages = extract_messages("not a list")
        assert messages == []

        # None
        messages = extract_messages(None)
        assert messages == []

        # List of non-dict items
        messages = extract_messages(["string", 123, None])
        assert messages == []

    def test_extract_signature_matches_interface(self):
        """Test that extract_messages has correct signature."""
        from db.importers.youtube import extract_messages
        import inspect

        sig = inspect.signature(extract_messages)
        params = list(sig.parameters.keys())

        # Should have watch_history_data as first parameter
        assert params[0] == "watch_history_data"
        # Should accept **kwargs for extensibility
        assert "kwargs" in params or any(
            p for p in sig.parameters.values() if p.kind == inspect.Parameter.VAR_KEYWORD
        )

    def test_parse_timestamp_iso_format(self):
        """Test ISO timestamp parsing."""
        from db.importers.youtube import parse_timestamp

        # Standard ISO format with Z timezone
        ts = parse_timestamp("2024-01-15T14:30:00.000Z")
        assert isinstance(ts, float)
        assert ts > 0

        # ISO format without milliseconds
        ts = parse_timestamp("2024-01-15T14:30:00Z")
        assert isinstance(ts, float)

    def test_parse_timestamp_handles_invalid_input(self):
        """Test timestamp parsing with invalid input."""
        from db.importers.youtube import parse_timestamp

        # Should return current time for invalid input
        ts = parse_timestamp("invalid")
        assert isinstance(ts, float)
        assert ts > 0

        # Empty string
        ts = parse_timestamp("")
        assert isinstance(ts, float)

    def test_extract_with_include_channel_option(self):
        """Test include_channel option."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Test Video",
                "titleUrl": "https://www.youtube.com/watch?v=test123",
                "time": "2024-01-15T14:30:00.000Z",
                "subtitles": [
                    {
                        "name": "Channel Name",
                        "url": "https://www.youtube.com/channel/UC123"
                    }
                ]
            }
        ]

        # With channel (default)
        messages = extract_messages(watch_history, include_channel=True)
        assert "by Channel Name" in messages[0]["content"]

        # Without channel
        messages = extract_messages(watch_history, include_channel=False)
        assert "by Channel Name" not in messages[0]["content"]
        assert messages[0]["content"] == "Watched: Test Video"

    def test_extract_handles_youtu_be_short_urls(self):
        """Test handling of youtu.be short URLs."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Short URL Video",
                "titleUrl": "https://youtu.be/abc123xyz",
                "time": "2024-01-15T14:30:00.000Z"
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 1
        assert messages[0]["metadata"]["video_id"] == "abc123xyz"

    def test_extract_all_messages_have_required_fields(self):
        """Test that all extracted messages have required fields."""
        from db.importers.youtube import extract_messages

        watch_history = [
            {
                "title": "Test Video",
                "titleUrl": "https://www.youtube.com/watch?v=test123",
                "time": "2024-01-15T14:30:00.000Z"
            }
        ]

        messages = extract_messages(watch_history)
        assert len(messages) == 1

        msg = messages[0]
        # Required fields
        assert "role" in msg
        assert "content" in msg
        assert "created_at" in msg
        assert "metadata" in msg

        # Metadata fields
        assert "video_id" in msg["metadata"]
        assert "video_url" in msg["metadata"]
        assert "transcript_status" in msg["metadata"]
