"""
Claude format message extractor.

Extracts messages from Claude's chat_messages list format.
Claude stores conversations as a list of messages with sender and text fields.
"""

from typing import Dict, List, Any, Optional
import re


def _clean_artifact_placeholders(text: str) -> str:
    """
    Remove Claude artifact placeholder messages from message text.

    Claude.ai shows placeholder messages when artifacts can't be displayed,
    but the actual artifact content is in the attachments. These placeholders
    should be removed from the message text.

    Args:
        text: Message text that may contain placeholder messages

    Returns:
        Cleaned text with placeholders removed
    """
    # List of placeholder patterns to remove
    # Note: Using DOTALL flag so . matches newlines inside code blocks
    # Note: Using . to match the apostrophe (either ASCII or Unicode curly quote)
    placeholders = [
        r'```.*?This block is not supported on your current device yet\..*?```',
        r'```.*?Viewing artifacts created via the Analysis Tool web feature preview isn.t yet supported on mobile\..*?```',
        r'This block is not supported on your current device yet\.',
        r'Viewing artifacts created via the Analysis Tool web feature preview isn.t yet supported on mobile\.',
    ]

    cleaned_text = text
    for pattern in placeholders:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)

    # Clean up extra whitespace
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)  # Replace 3+ newlines with 2
    cleaned_text = cleaned_text.strip()

    return cleaned_text


def extract_messages(conversation_data: Optional[List], **kwargs) -> List[Dict]:
    """
    Extract messages from Claude format conversation data.
    
    Args:
        conversation_data: Claude conversation with list of chat_messages
                          Each message has: sender, text, created_at (optional), attachments, files
        **kwargs: Additional options (for extensibility)
        
    Returns:
        List of message dicts with keys:
        - role: 'user' or 'assistant' (human sender -> user, others -> assistant)
        - content: message text
        - created_at: ISO timestamp string (optional)
        - attachments: List of attachment dicts (if present)
    """
    # Handle None or non-list input
    if conversation_data is None or not isinstance(conversation_data, list):
        return []
    
    messages = []
    
    for msg_data in conversation_data:
        # Skip None entries
        if msg_data is None or not isinstance(msg_data, dict):
            continue
        
        # Extract sender - required field
        sender = msg_data.get('sender')
        if sender is None:
            continue
        
        # Extract text content - required field
        text = msg_data.get('text', '')

        # Skip empty or whitespace-only messages
        if not text or not text.strip():
            continue

        # Clean artifact placeholder messages from text
        text = _clean_artifact_placeholders(text)

        # Skip if text is now empty after cleaning
        if not text or not text.strip():
            continue

        # Map sender to role: human -> user, everything else -> assistant
        role = 'user' if sender == 'human' else 'assistant'

        # Build message dict with required fields
        msg_dict = {
            'role': role,
            'content': text
        }
        
        # Preserve timestamp if available (ISO format string)
        created_at = msg_data.get('created_at')
        if created_at:
            msg_dict['created_at'] = created_at
        
        # Extract attachments if present
        from controllers.postgres_controller import extract_claude_attachments
        attachments = extract_claude_attachments(msg_data)
        if attachments:
            msg_dict['attachments'] = attachments
        
        messages.append(msg_dict)
    
    return messages
