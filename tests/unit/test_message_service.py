"""
Test the message service with outbox pattern for atomic writes.
"""

import os
import sys
import logging
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from db.services.message_service import MessageService, create_message_atomically
from db.repositories.unit_of_work import get_unit_of_work

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_outbox_pattern(uow):
    """Test the outbox pattern for atomic message creation with job enqueuing."""
    logger.info("Testing outbox pattern...")
    
    # Create a conversation for testing
    conversation = uow.conversations.create(title="Test Outbox Pattern")
    uow.session.flush()
    logger.info(f"Created test conversation: {conversation.id}")
    conversation_id = conversation.id
    
    # Test 1: Create message atomically with embedding job
    logger.info("\n--- Test 1: Atomic Message Creation ---")
    
    # Create message directly in UoW
    message = uow.messages.create(
        conversation_id=conversation_id,
        role='user',
        content='This is a test message for the outbox pattern.',
        message_metadata={'test': True, 'timestamp': datetime.utcnow().isoformat()}
    )
    message_id = message.id
    
    # Enqueue embedding job in same transaction
    job_payload = {
        'message_id': str(message.id),
        'conversation_id': str(conversation_id),
        'content': 'This is a test message for the outbox pattern.',
        'model': 'all-MiniLM-L6-v2'
    }
    uow.jobs.enqueue(kind='generate_embedding', payload=job_payload)
    uow.session.flush()
    
    # Verify message was created
    retrieved_message = uow.messages.get_by_id(message_id)
    assert retrieved_message is not None
    assert retrieved_message.content == 'This is a test message for the outbox pattern.'
    
    # Verify embedding job was enqueued
    pending_jobs = uow.jobs.get_pending_jobs(kinds=['generate_embedding'])
    embedding_jobs_for_message = [
        job for job in pending_jobs
        if job.payload.get('message_id') == str(message_id)
    ]
    
    assert len(embedding_jobs_for_message) == 1
    job = embedding_jobs_for_message[0]
    assert job.kind == 'generate_embedding'
    assert job.payload['content'] == 'This is a test message for the outbox pattern.'
    assert job.payload['model'] == 'all-MiniLM-L6-v2'
    
    logger.info(f"✓ Message created: {message_id}")
    logger.info(f"✓ Embedding job enqueued: {job.id}")
    
    # Test 2: Update message and enqueue new job for content change
    logger.info("\n--- Test 2: Message Update with Content Change ---")
    
    updated_content = 'This is the updated content for testing.'
    updated_message = uow.messages.update(
        message_id,
        content=updated_content,
        message_metadata={'test': True, 'updated': True}
    )
    
    # Enqueue new embedding job for updated content
    update_job_payload = {
        'message_id': str(message_id),
        'conversation_id': str(conversation_id),
        'content': updated_content,
        'model': 'all-MiniLM-L6-v2'
    }
    uow.jobs.enqueue(kind='generate_embedding', payload=update_job_payload)
    uow.session.flush()
    
    # Verify message was updated
    retrieved_message = uow.messages.get_by_id(message_id)
    assert retrieved_message.content == updated_content
    assert retrieved_message.message_metadata['updated'] is True
    
    # Verify we now have 2 jobs
    all_jobs = uow.jobs.get_pending_jobs(kinds=['generate_embedding'])
    message_jobs = [j for j in all_jobs if j.payload.get('message_id') == str(message_id)]
    assert len(message_jobs) == 2
    
    logger.info(f"✓ Message updated with new embedding job")
    
    # Test 3: Bulk message creation
    logger.info("\n--- Test 3: Bulk Message Creation ---")
    
    bulk_messages = []
    for i in range(1, 4):
        msg = uow.messages.create(
            conversation_id=conversation_id,
            role='user' if i % 2 else 'assistant',
            content=f'Bulk message {i}',
            message_metadata={'bulk': True, 'order': i}
        )
        bulk_messages.append(msg)
        
        # Enqueue job for each message
        job_payload = {
            'message_id': str(msg.id),
            'conversation_id': str(conversation_id),
            'content': msg.content,
            'model': 'all-MiniLM-L6-v2'
        }
        uow.jobs.enqueue(kind='generate_embedding', payload=job_payload)
    
    uow.session.flush()
    
    # Verify all messages and jobs created
    assert len(bulk_messages) == 3
    bulk_ids = [str(m.id) for m in bulk_messages]
    all_jobs = uow.jobs.get_pending_jobs(kinds=['generate_embedding'])
    bulk_jobs = [j for j in all_jobs if j.payload.get('message_id') in bulk_ids]
    assert len(bulk_jobs) == 3
    
    logger.info(f"✓ Created {len(bulk_messages)} messages with {len(bulk_jobs)} jobs")
    
    logger.info("\n🎉 All outbox pattern tests passed!")
