"""
YouTube watch history format message extractor.

Extracts messages from YouTube watch history exported via Google Takeout.
YouTube watch history is a list of watched videos with metadata like title, URL, time, and channel info.
"""

from typing import Dict, List, Any
from datetime import datetime
import re


def extract_video_id(url: str) -> str:
    """
    Extract YouTube video ID from URL.

    Args:
        url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)

    Returns:
        Video ID string or empty string if not found
    """
    if not url:
        return ""

    # Match various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\?/]+)',
        r'youtube\.com/embed/([^&\?/]+)',
        r'youtube\.com/v/([^&\?/]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return ""


def parse_timestamp(time_str: str) -> float:
    """
    Parse ISO timestamp from YouTube watch history.

    Args:
        time_str: ISO timestamp string (e.g., "2023-10-15T14:30:00.000Z")

    Returns:
        Unix timestamp as float
    """
    try:
        # Parse ISO format with Z timezone
        if time_str.endswith('Z'):
            time_str = time_str[:-1] + '+00:00'

        dt = datetime.fromisoformat(time_str)
        return dt.timestamp()
    except (ValueError, AttributeError):
        # Return current time if parsing fails
        return datetime.now().timestamp()


def extract_messages(watch_history_data: List[Dict], **kwargs) -> List[Dict]:
    """
    Extract messages from YouTube watch history data.

    Args:
        watch_history_data: List of watch history items from Google Takeout
                           Each item has:
                           - title: Video title
                           - titleUrl: YouTube video URL
                           - time: ISO timestamp
                           - subtitles: (optional) Channel info

        **kwargs: Additional options:
                  - group_by_day: Group videos watched on the same day (default: False)
                  - include_channel: Include channel name in content (default: True)

    Returns:
        List of message dicts with keys:
        - role: Always 'user' (watch events are user actions)
        - content: Video title and watch context
        - created_at: Unix epoch timestamp
        - metadata: dict with video_id, channel, url, transcript_status
    """
    if not isinstance(watch_history_data, list):
        return []

    # Extract options
    group_by_day = kwargs.get('group_by_day', False)
    include_channel = kwargs.get('include_channel', True)

    messages = []

    for item in watch_history_data:
        if not isinstance(item, dict):
            continue

        # Extract basic fields
        title = item.get('title', '').strip()
        title_url = item.get('titleUrl', '')
        time_str = item.get('time', '')

        # Skip items without essential data
        if not title or not title_url:
            continue

        # Extract video ID from URL
        video_id = extract_video_id(title_url)
        if not video_id:
            continue

        # Parse timestamp
        created_at = parse_timestamp(time_str)

        # Extract channel info if available
        channel_name = ""
        channel_url = ""
        subtitles = item.get('subtitles', [])
        if subtitles and isinstance(subtitles, list) and len(subtitles) > 0:
            subtitle = subtitles[0]
            if isinstance(subtitle, dict):
                channel_name = subtitle.get('name', '')
                channel_url = subtitle.get('url', '')

        # Build content string
        content_parts = [f"Watched: {title}"]
        if include_channel and channel_name:
            content_parts.append(f"by {channel_name}")

        content = " ".join(content_parts)

        # Build metadata
        metadata = {
            'video_id': video_id,
            'video_url': title_url,
            'transcript_status': 'pending',  # Will be populated by transcription worker
            'transcript': None,
            'summary': None,
        }

        if channel_name:
            metadata['channel_name'] = channel_name
        if channel_url:
            metadata['channel_url'] = channel_url

        # Create message dict
        msg_dict = {
            'role': 'user',  # Watch events are user actions
            'content': content,
            'created_at': created_at,
            'metadata': metadata,
        }

        messages.append(msg_dict)

    # Sort by timestamp (oldest first)
    messages.sort(key=lambda m: m.get('created_at', 0))

    return messages
