"""
Test Data Seeding Utilities

Factory functions for creating realistic test data for conversations, messages,
embeddings, jobs, and settings.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from db.models.models import Conversation, Message, MessageEmbedding, Job, Setting
from db.repositories.unit_of_work import UnitOfWork
from tests.utils.fake_embeddings import generate_fake_embedding


# Sample conversation titles and content
SAMPLE_TITLES = [
    "Python Web Scraping Help",
    "Database Design Review",
    "Machine Learning Tutorial",
    "React Component Best Practices",
    "PostgreSQL Performance Tuning",
    "Docker Compose Configuration",
    "API Design Patterns",
    "Testing Strategies Discussion",
    "Code Review Feedback",
    "Deployment Architecture Planning"
]

SAMPLE_USER_MESSAGES = [
    "How do I implement this feature?",
    "Can you help me debug this error?",
    "What's the best approach for this problem?",
    "I'm trying to understand how this works.",
    "Could you review my implementation?",
    "What are the trade-offs of different approaches?",
    "How can I optimize this code?",
    "Is there a better way to structure this?",
    "Can you explain this concept?",
    "What tools do you recommend?"
]

SAMPLE_ASSISTANT_MESSAGES = [
    "Here's how you can approach this problem...",
    "Let me help you understand the error...",
    "I recommend the following approach...",
    "This is how it works under the hood...",
    "Your implementation looks good, but consider...",
    "There are several trade-offs to consider...",
    "You can optimize this by...",
    "A better structure would be...",
    "Let me explain this concept step by step...",
    "I suggest using these tools..."
]


def create_conversation(
    uow: UnitOfWork,
    title: Optional[str] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None
) -> Conversation:
    """
    Create a test conversation.
    
    Args:
        uow: Unit of work for database operations
        title: Conversation title (random if None)
        created_at: Creation timestamp (now if None)
        updated_at: Update timestamp (created_at if None)
        
    Returns:
        Created Conversation instance
    """
    import random
    
    if title is None:
        title = random.choice(SAMPLE_TITLES)
    
    kwargs = {"title": title}
    if created_at:
        kwargs["created_at"] = created_at
    if updated_at:
        kwargs["updated_at"] = updated_at
    
    conversation = uow.conversations.create(**kwargs)
    uow.session.flush()
    
    return conversation


def create_message(
    uow: UnitOfWork,
    conversation_id: UUID,
    role: str = "user",
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    created_at: Optional[datetime] = None,
    with_embedding: bool = False
) -> Message:
    """
    Create a test message.
    
    Args:
        uow: Unit of work
        conversation_id: ID of parent conversation
        role: Message role (user, assistant, system)
        content: Message content (random if None)
        metadata: Message metadata
        created_at: Creation timestamp
        with_embedding: Whether to create embedding for this message
        
    Returns:
        Created Message instance
    """
    import random
    
    if content is None:
        if role == "user":
            content = random.choice(SAMPLE_USER_MESSAGES)
        else:
            content = random.choice(SAMPLE_ASSISTANT_MESSAGES)
    
    kwargs = {
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "message_metadata": metadata or {}
    }
    
    if created_at:
        kwargs["created_at"] = created_at
    
    message = uow.messages.create(**kwargs)
    uow.session.flush()
    
    if with_embedding:
        create_embedding(uow, message.id, content)
    
    return message


def create_embedding(
    uow: UnitOfWork,
    message_id: UUID,
    content: str,
    model: str = "all-MiniLM-L6-v2"
) -> MessageEmbedding:
    """
    Create a test embedding using fake embedding generator.
    
    Args:
        uow: Unit of work
        message_id: ID of parent message
        content: Text content to embed
        model: Embedding model name
        
    Returns:
        Created MessageEmbedding instance
    """
    # Generate fake embedding
    embedding_vector = generate_fake_embedding(content)
    
    embedding = uow.embeddings.create(
        message_id=message_id,
        embedding=embedding_vector,
        model=model
    )
    uow.session.flush()
    
    return embedding


def seed_conversation_with_embeddings(
    session,
    title: str,
    messages: List[tuple[str, str]],
    embedding_generator=None,
    created_at: Optional[datetime] = None
) -> Conversation:
    """
    Seed a conversation with messages and embeddings.
    
    Args:
        session: Database session
        title: Conversation title
        messages: List of (role, content) tuples
        embedding_generator: Optional FakeEmbeddingGenerator instance
        created_at: Optional creation timestamp
    
    Returns:
        Created Conversation with messages and embeddings
    """
    from tests.utils.fake_embeddings import FakeEmbeddingGenerator
    
    if embedding_generator is None:
        embedding_generator = FakeEmbeddingGenerator()
    
    # Create conversation
    conversation = Conversation(
        id=uuid4(),
        title=title,
        created_at=created_at or datetime.now(timezone.utc),
        updated_at=created_at or datetime.now(timezone.utc)
    )
    session.add(conversation)
    session.flush()
    
    # Create messages with embeddings
    for role, content in messages:
        message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=role,
            content=content,
            message_metadata={},
            created_at=datetime.now(timezone.utc)
        )
        session.add(message)
        session.flush()
        
        # Generate embedding
        embedding_vector = embedding_generator.generate_embedding(content)
        embedding = MessageEmbedding(
            message_id=message.id,
            embedding=embedding_vector,
            model="all-MiniLM-L6-v2"
        )
        session.add(embedding)
    
    session.flush()
    return conversation


def create_job(
    uow: UnitOfWork,
    kind: str = "generate_embedding",
    payload: Optional[Dict[str, Any]] = None,
    status: str = "pending"
) -> Job:
    """
    Create a test job.
    
    Args:
        uow: Unit of work
        kind: Job kind/type
        payload: Job payload data
        status: Job status
        
    Returns:
        Created Job instance
    """
    job = uow.jobs.enqueue(
        kind=kind,
        payload=payload or {}
    )
    
    if status != "pending":
        uow.jobs.update(job.id, status=status)
        uow.session.flush()
    
    return job


def create_setting(
    uow: UnitOfWork,
    key: str,
    value: str,
    description: Optional[str] = None,
    category: str = "general"
) -> Setting:
    """
    Create a test setting.
    
    Args:
        uow: Unit of work
        key: Setting key/ID
        value: Setting value
        description: Setting description
        category: Setting category
        
    Returns:
        Created Setting instance
    """
    setting = uow.settings.create(
        id=key,
        value=value,
        description=description,
        category=category
    )
    uow.session.flush()
    
    return setting


def seed_conversation_with_messages(
    uow: UnitOfWork,
    title: Optional[str] = None,
    message_count: int = 4,
    with_embeddings: bool = False,
    created_days_ago: int = 0
) -> tuple[Conversation, List[Message]]:
    """
    Seed a complete conversation with messages.
    
    Args:
        uow: Unit of work
        title: Conversation title
        message_count: Number of messages to create
        with_embeddings: Whether to create embeddings
        created_days_ago: How many days ago the conversation was created
        
    Returns:
        Tuple of (Conversation, List of Messages)
    """
    base_time = datetime.now(timezone.utc) - timedelta(days=created_days_ago)
    
    conversation = create_conversation(
        uow,
        title=title,
        created_at=base_time
    )
    
    messages = []
    for i in range(message_count):
        role = "user" if i % 2 == 0 else "assistant"
        message_time = base_time + timedelta(minutes=i * 2)
        
        message = create_message(
            uow,
            conversation.id,
            role=role,
            created_at=message_time,
            with_embedding=with_embeddings
        )
        messages.append(message)
    
    return conversation, messages


def seed_multiple_conversations(
    uow: UnitOfWork,
    count: int = 10,
    messages_per_conversation: int = 4,
    with_embeddings: bool = False
) -> List[tuple[Conversation, List[Message]]]:
    """
    Seed multiple conversations with messages.
    
    Args:
        uow: Unit of work
        count: Number of conversations to create
        messages_per_conversation: Messages per conversation
        with_embeddings: Whether to create embeddings
        
    Returns:
        List of (Conversation, Messages) tuples
    """
    conversations = []
    
    for i in range(count):
        conv, messages = seed_conversation_with_messages(
            uow,
            message_count=messages_per_conversation,
            with_embeddings=with_embeddings,
            created_days_ago=count - i  # Spread over time
        )
        conversations.append((conv, messages))
    
    return conversations


def seed_test_corpus(
    uow: UnitOfWork,
    with_embeddings: bool = True
) -> Dict[str, Any]:
    """
    Seed a curated test corpus for search testing.
    
    Creates conversations with specific content for validating search functionality.
    
    Args:
        uow: Unit of work
        with_embeddings: Whether to create embeddings
        
    Returns:
        Dict with created conversations and metadata
    """
    test_data = {
        "conversations": [],
        "total_messages": 0
    }
    
    # Python-related conversation
    conv1, msgs1 = seed_conversation_with_messages(
        uow,
        title="Python Web Scraping Tutorial",
        message_count=6,
        with_embeddings=with_embeddings,
        created_days_ago=5
    )
    
    # Update messages with specific content
    msgs1[0].content = "How do I scrape a website with Python?"
    msgs1[1].content = "You can use libraries like Beautiful Soup and requests for web scraping..."
    msgs1[2].content = "What about JavaScript-heavy sites?"
    msgs1[3].content = "For JavaScript-heavy sites, you'll need Selenium or Playwright..."
    uow.session.flush()
    
    test_data["conversations"].append(("python", conv1, msgs1))
    test_data["total_messages"] += len(msgs1)
    
    # Database-related conversation
    conv2, msgs2 = seed_conversation_with_messages(
        uow,
        title="PostgreSQL Performance Optimization",
        message_count=4,
        with_embeddings=with_embeddings,
        created_days_ago=3
    )
    
    msgs2[0].content = "How can I optimize my PostgreSQL queries?"
    msgs2[1].content = "Start by analyzing query plans with EXPLAIN ANALYZE..."
    uow.session.flush()
    
    test_data["conversations"].append(("database", conv2, msgs2))
    test_data["total_messages"] += len(msgs2)
    
    # Machine learning conversation
    conv3, msgs3 = seed_conversation_with_messages(
        uow,
        title="Machine Learning Basics",
        message_count=4,
        with_embeddings=with_embeddings,
        created_days_ago=1
    )
    
    msgs3[0].content = "What's the difference between supervised and unsupervised learning?"
    msgs3[1].content = "Supervised learning uses labeled data for training..."
    uow.session.flush()
    
    test_data["conversations"].append(("ml", conv3, msgs3))
    test_data["total_messages"] += len(msgs3)
    
    return test_data


def clear_test_data(uow: UnitOfWork):
    """
    Clear all test data from database.
    
    Args:
        uow: Unit of work
    """
    # Delete in correct order due to foreign keys
    uow.session.execute("DELETE FROM message_embeddings")
    uow.session.execute("DELETE FROM messages")
    uow.session.execute("DELETE FROM conversations")
    uow.session.execute("DELETE FROM jobs")
    uow.session.execute("DELETE FROM settings")
    uow.session.flush()
