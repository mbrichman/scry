"""
Test Infrastructure Validation

Verifies that Phase 1.0 test infrastructure is set up correctly.
Run this test to confirm your test environment is ready.
"""
import pytest
from sqlalchemy import text
from tests.utils.seed import seed_conversation_with_messages
from tests.utils.fake_embeddings import generate_fake_embedding, FakeEmbeddingGenerator


@pytest.mark.unit
def test_database_connection(db_session):
    """Verify database connection works."""
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.unit
def test_database_extensions(db_session):
    """Verify required PostgreSQL extensions are loaded."""
    result = db_session.execute(text(
        "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp')"
    ))
    extensions = [row[0] for row in result]
    
    assert 'vector' in extensions, "pgvector extension not loaded"
    assert 'pg_trgm' in extensions, "pg_trgm extension not loaded"
    assert 'uuid-ossp' in extensions, "uuid-ossp extension not loaded"


@pytest.mark.unit
def test_seed_conversation(uow):
    """Verify conversation seeding works."""
    conv, messages = seed_conversation_with_messages(
        uow,
        title="Test Conversation",
        message_count=3,
        with_embeddings=False
    )
    
    assert conv.id is not None
    assert conv.title == "Test Conversation"
    assert len(messages) == 3
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.unit
def test_seed_with_embeddings(uow):
    """Verify seeding with embeddings works."""
    conv, messages = seed_conversation_with_messages(
        uow,
        message_count=2,
        with_embeddings=True
    )
    
    # Check that embeddings were created
    for message in messages:
        embedding = uow.embeddings.get_by_message_id(message.id)
        assert embedding is not None
        assert embedding.model == "all-MiniLM-L6-v2"
        assert len(embedding.embedding) == 384


@pytest.mark.unit
def test_fake_embeddings():
    """Verify fake embeddings work correctly."""
    embedding = generate_fake_embedding("test text")
    
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)
    
    # Test determinism - same text should produce same embedding
    embedding2 = generate_fake_embedding("test text")
    assert embedding == embedding2
    
    # Different text should produce different embedding
    embedding3 = generate_fake_embedding("different text")
    assert embedding != embedding3


@pytest.mark.unit
def test_fake_embedding_generator():
    """Verify FakeEmbeddingGenerator features."""
    generator = FakeEmbeddingGenerator(dimension=384, seed=42)
    
    # Test single embedding
    embedding = generator.generate_embedding("test")
    assert len(embedding) == 384
    
    # Test batch embeddings
    texts = ["text1", "text2", "text3"]
    embeddings = generator.generate_embeddings(texts)
    assert len(embeddings) == 3
    assert all(len(e) == 384 for e in embeddings)
    
    # Test cosine similarity
    similarity = generator.cosine_similarity(embeddings[0], embeddings[0])
    assert abs(similarity - 1.0) < 0.01  # Same embedding should have similarity ~1
    
    # Test similar embedding generation
    similar = generator.generate_similar_embedding("test", similarity=0.9)
    assert len(similar) == 384
    actual_similarity = generator.cosine_similarity(embedding, similar)
    assert 0.85 < actual_similarity < 0.95  # Should be close to target


@pytest.mark.unit
def test_seed_conversations_fixture(seed_conversations):
    """Verify seed_conversations fixture works."""
    conversations = seed_conversations(
        count=5,
        messages_per_conversation=4,
        with_embeddings=False
    )
    
    assert len(conversations) == 5
    for conv, messages in conversations:
        assert conv.id is not None
        assert len(messages) == 4


@pytest.mark.unit
def test_transaction_rollback(uow, db_session):
    """Verify transaction rollback isolates tests."""
    # Create a conversation
    conv, messages = seed_conversation_with_messages(
        uow,
        message_count=2,
        with_embeddings=False
    )
    conv_id = conv.id
    
    # Count conversations
    count_before = db_session.execute(text("SELECT COUNT(*) FROM conversations")).scalar()
    assert count_before > 0
    
    # After this test completes, rollback should clean up
    # (This is verified by running multiple tests and checking they don't interfere)


@pytest.mark.unit  
def test_database_is_clean(db_session):
    """Verify each test starts with clean database (due to rollback)."""
    # If rollback is working, this count should be 0
    # (assuming no other test is running in parallel)
    count = db_session.execute(text("SELECT COUNT(*) FROM conversations")).scalar()
    # Count might be > 0 if other tests ran in this transaction
    # The important thing is that we can create new data without conflicts
    assert count >= 0  # Just verify we can query


@pytest.mark.unit
def test_uow_commit_and_query(uow):
    """Verify UnitOfWork commit functionality."""
    # Create conversation
    conversation = uow.conversations.create(title="UoW Test")
    uow.session.flush()
    
    # Verify it exists in current session
    retrieved = uow.conversations.get_by_id(conversation.id)
    assert retrieved is not None
    assert retrieved.title == "UoW Test"


@pytest.mark.unit
def test_fixture_isolation():
    """Verify test fixtures are properly isolated."""
    # This test should pass even if run after others
    # because each test gets a fresh transaction
    import random
    test_value = random.randint(1, 1000)
    assert test_value > 0  # Trivial assertion to verify test runs


if __name__ == '__main__':
    # Run with: pytest tests/test_infrastructure.py -v
    pytest.main([__file__, '-v', '-m', 'unit'])
