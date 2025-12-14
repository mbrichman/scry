#!/usr/bin/env python3
"""
Delete all OpenWebUI conversations from prod via API.

This script finds all conversations where the messages have 'source': 'openwebui'
in their metadata, then deletes those conversations via the API.

Usage:
    python scripts/delete_openwebui_conversations.py [--dry-run] [--api-url URL]

Environment:
    Set API_URL env var or use --api-url flag. Defaults to http://localhost:5000
"""

import os
import sys
import json
import argparse
import requests
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_openwebui_conversations(api_url: str) -> List[Dict[str, Any]]:
    """
    Find all conversations that contain OpenWebUI messages using API source filter.
    
    Args:
        api_url: Base URL of the API (e.g., http://localhost:5000)
    
    Returns:
        List of conversation objects with OpenWebUI messages
    """
    logger.info("Fetching OpenWebUI conversations...")
    
    try:
        # Use API source_filter parameter to get only openwebui conversations
        response = requests.get(
            f"{api_url}/api/conversations",
            params={'source_filter': 'openwebui'},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        # API returns {"documents": [...], "metadatas": [...], "ids": [...]}
        if not isinstance(result, dict):
            logger.error(f"Expected dict response, got {type(result)}")
            return []
        
        ids = result.get('ids', [])
        metadatas = result.get('metadatas', [])
        
        openwebui_convs = []
        
        for conv_id, metadata in zip(ids, metadatas):
            title = metadata.get('title', 'Unknown')
            message_count = metadata.get('message_count', 0)
            source = metadata.get('source', 'unknown')
            
            # Double-check it's actually openwebui
            if source.lower() == 'openwebui':
                openwebui_convs.append({
                    'id': conv_id,
                    'title': title,
                    'message_count': message_count
                })
                logger.info(f"Found OpenWebUI conversation: {title} ({message_count} messages)")
        
        return openwebui_convs
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return []
    except (KeyError, TypeError) as e:
        logger.error(f"Failed to parse API response: {e}")
        return []


def delete_conversations(api_url: str, conversations: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """
    Delete conversations via API.
    
    Args:
        api_url: Base URL of the API
        conversations: List of conversation dicts with 'id' and 'title'
        dry_run: If True, only show what would be deleted
    
    Returns:
        Number of successfully deleted conversations
    """
    deleted_count = 0
    
    for conv in conversations:
        conv_id = conv['id']
        title = conv['title']
        
        if dry_run:
            logger.info(f"[DRY RUN] Would delete: {title} ({conv_id})")
            deleted_count += 1
        else:
            try:
                logger.info(f"Deleting: {title}...")
                response = requests.delete(f"{api_url}/api/conversation/{conv_id}", timeout=30)
                response.raise_for_status()
                logger.info(f"✅ Deleted: {title}")
                deleted_count += 1
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Failed to delete {title}: {e}")
    
    return deleted_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Delete all OpenWebUI conversations from prod'
    )
    parser.add_argument(
        '--api-url',
        default=os.getenv('API_URL', 'http://localhost:5000'),
        help='API base URL (default: http://localhost:5000 or API_URL env var)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Using API URL: {args.api_url}")
    logger.info(f"Dry run: {args.dry_run}")
    
    # Find OpenWebUI conversations
    openwebui_convs = find_openwebui_conversations(args.api_url)
    
    if not openwebui_convs:
        logger.info("No OpenWebUI conversations found")
        return 0
    
    logger.info(f"\nFound {len(openwebui_convs)} OpenWebUI conversations:")
    for conv in openwebui_convs:
        logger.info(f"  - {conv['title']} ({conv['message_count']} messages)")
    
    # Confirm deletion
    if not args.dry_run:
        response = input(f"\nAre you sure you want to delete {len(openwebui_convs)} conversations? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Cancelled")
            return 0
    
    # Delete conversations
    logger.info(f"\n{'[DRY RUN] ' if args.dry_run else ''}Deleting conversations...\n")
    deleted = delete_conversations(args.api_url, openwebui_convs, args.dry_run)
    
    logger.info(f"\n{'[DRY RUN] ' if args.dry_run else ''}Total: {deleted} conversations {'would be deleted' if args.dry_run else 'deleted'}")
    return deleted


if __name__ == '__main__':
    sys.exit(main())
