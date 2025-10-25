"""
Utility for parsing Word documents containing chat conversations.

Adapted from the legacy ChromaDB implementation to work with PostgreSQL backend.
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from docx import Document


def extract_timestamp(text: str) -> Optional[str]:
    """
    Try to extract timestamps from text using regex.
    
    Returns ISO format timestamp string if found, None otherwise.
    """
    # Look for common date formats
    date_patterns = [
        (r"(\d{4}-\d{2}-\d{2})", "%Y-%m-%d"),  # YYYY-MM-DD
        (r"(\d{2}/\d{2}/\d{4})", "%m/%d/%Y"),  # MM/DD/YYYY
        (r"(\w+ \d{1,2}, \d{4})", "%B %d, %Y"),  # Month DD, YYYY
    ]

    for pattern, fmt in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                dt = datetime.strptime(matches[0], fmt)
                return dt.isoformat()
            except ValueError:
                continue
    
    return None


def clean_text_content(text: str) -> str:
    """Clean up text content by removing extra whitespace."""
    # Clean up non-breaking spaces and other Unicode issues
    text = text.replace('\xa0', ' ').replace('\u00a0', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_docx_file(file_path: str) -> Tuple[List[Dict], List[str], str]:
    """
    Parse a Word document containing a chat conversation.
    
    Args:
        file_path: Path to the .docx file
        
    Returns:
        Tuple of (messages, timestamps, title) where:
        - messages: List of dicts with 'role' and 'content' keys
        - timestamps: List of ISO timestamp strings extracted from document
        - title: Document title (filename without extension)
    """
    doc = Document(file_path)
    
    messages = []
    timestamps = []
    current_role = None
    current_content = []

    for p in doc.paragraphs:
        text = p.text.strip()
        text = clean_text_content(text)
        
        if not text:
            # Empty paragraph - save current message if any
            if current_role and current_content:
                messages.append({
                    'role': current_role,
                    'content': '\n'.join(current_content)
                })
                current_content = []
            continue

        # Extract potential timestamp
        ts = extract_timestamp(text)
        if ts:
            timestamps.append(ts)

        # Check if this is a role indicator
        # Handle formats: "You:", "ChatGPT said:", "User", "Assistant:", etc.
        role_match = re.match(
            r"^(You|ChatGPT|User|Assistant|System)(\s+said)?:?\s*$",
            text,
            re.IGNORECASE,
        )
        
        if role_match:
            # Save previous content if any
            if current_role and current_content:
                messages.append({
                    'role': current_role,
                    'content': '\n'.join(current_content)
                })

            # Normalize the role name to match expected values
            raw_role = role_match.group(1).lower()
            if raw_role == 'you':
                current_role = 'user'
            elif raw_role == 'chatgpt':
                current_role = 'assistant'
            elif raw_role == 'assistant':
                current_role = 'assistant'
            elif raw_role == 'user':
                current_role = 'user'
            elif raw_role == 'system':
                current_role = 'system'
            else:
                current_role = 'assistant'  # Default
            
            current_content = []
        else:
            # Add to current content
            if current_role:
                cleaned_text = clean_text_content(text)
                if cleaned_text:
                    current_content.append(cleaned_text)

    # Don't forget the last message
    if current_role and current_content:
        messages.append({
            'role': current_role,
            'content': '\n'.join(current_content)
        })

    # Extract title from filename
    import os
    title = os.path.splitext(os.path.basename(file_path))[0]

    return messages, timestamps, title
