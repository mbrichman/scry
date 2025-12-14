"""initial schema with conversations messages and embeddings

Revision ID: 0bf3d3250afa
Revises: 
Create Date: 2025-10-06 21:02:50.346406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bf3d3250afa'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable required extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), server_default=sa.text("'{}'"), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='messages_role_check')
    )
    
    # Add generated tsvector column for FTS
    op.execute(
        "ALTER TABLE messages ADD COLUMN message_search TSVECTOR "
        "GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED"
    )
    
    # Create message_embeddings table
    op.create_table(
        'message_embeddings',
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('model', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('message_id')
    )
    
    # Add vector column separately (works better with extensions)
    op.execute('ALTER TABLE message_embeddings ADD COLUMN embedding VECTOR(384)')
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('kind', sa.Text(), nullable=False),
        sa.Column('payload', sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('status', sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column('attempts', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('not_before', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed')", name='jobs_status_check')
    )
    
    # Create indexes
    # Conversations indexes
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'], postgresql_using='btree')
    op.create_index('idx_conversations_updated_at', 'conversations', ['updated_at'], postgresql_using='btree')
    
    # Messages indexes
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_conv_created', 'messages', ['conversation_id', 'created_at'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_messages_role', 'messages', ['role'])
    
    # Full-text search indexes
    op.create_index('idx_messages_fts', 'messages', ['message_search'], postgresql_using='gin')
    op.create_index('idx_messages_trgm', 'messages', ['content'], postgresql_using='gin', postgresql_ops={'content': 'gin_trgm_ops'})
    
    # Job queue indexes
    op.create_index('idx_jobs_status_kind', 'jobs', ['status', 'kind'])
    op.create_index('idx_jobs_not_before', 'jobs', ['not_before'], postgresql_where="status = 'pending'")
    op.create_index('idx_jobs_created_at', 'jobs', ['created_at'])
    
    # Embeddings indexes
    op.create_index('idx_embeddings_model', 'message_embeddings', ['model'])
    op.create_index('idx_embeddings_updated_at', 'message_embeddings', ['updated_at'])
    
    # Create functions and triggers
    # Auto-update updated_at function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Version increment function
    op.execute("""
        CREATE OR REPLACE FUNCTION increment_message_version()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.content != NEW.content THEN
                NEW.version = OLD.version + 1;
                NEW.updated_at = NOW();
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers
    op.execute(
        "CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations "
        "FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    )
    op.execute(
        "CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages "
        "FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    )
    op.execute(
        "CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs "
        "FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    )
    op.execute(
        "CREATE TRIGGER update_message_embeddings_updated_at BEFORE UPDATE ON message_embeddings "
        "FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    )
    op.execute(
        "CREATE TRIGGER increment_message_version_trigger BEFORE UPDATE ON messages "
        "FOR EACH ROW EXECUTE FUNCTION increment_message_version()"
    )
    
    # Create helper views
    op.execute("""
        CREATE VIEW conversation_summaries AS
        SELECT 
            c.id,
            c.title,
            c.created_at,
            c.updated_at,
            COUNT(m.id) as message_count,
            MIN(m.created_at) as earliest_message_at,
            MAX(m.created_at) as latest_message_at,
            LEFT(COALESCE(
                (SELECT content FROM messages WHERE conversation_id = c.id ORDER BY created_at LIMIT 1),
                ''
            ), 200) as preview
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        GROUP BY c.id, c.title, c.created_at, c.updated_at
    """)
    
    op.execute("""
        CREATE VIEW embedding_coverage AS
        SELECT 
            COUNT(m.id) as total_messages,
            COUNT(e.message_id) as embedded_messages,
            ROUND(COUNT(e.message_id)::numeric / NULLIF(COUNT(m.id), 0) * 100, 2) as coverage_percent,
            COUNT(CASE WHEN e.updated_at < m.updated_at THEN 1 END) as stale_embeddings
        FROM messages m
        LEFT JOIN message_embeddings e ON m.id = e.message_id
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop views
    op.execute('DROP VIEW IF EXISTS embedding_coverage')
    op.execute('DROP VIEW IF EXISTS conversation_summaries')
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS increment_message_version_trigger ON messages')
    op.execute('DROP TRIGGER IF EXISTS update_message_embeddings_updated_at ON message_embeddings')
    op.execute('DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs')
    op.execute('DROP TRIGGER IF EXISTS update_messages_updated_at ON messages')
    op.execute('DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations')
    
    # Drop functions
    op.execute('DROP FUNCTION IF EXISTS increment_message_version()')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop indexes (most will be dropped automatically with tables)
    op.drop_index('idx_embeddings_updated_at', table_name='message_embeddings')
    op.drop_index('idx_embeddings_model', table_name='message_embeddings')
    op.drop_index('idx_jobs_created_at', table_name='jobs')
    op.drop_index('idx_jobs_not_before', table_name='jobs')
    op.drop_index('idx_jobs_status_kind', table_name='jobs')
    op.drop_index('idx_messages_trgm', table_name='messages')
    op.drop_index('idx_messages_fts', table_name='messages')
    op.drop_index('idx_messages_role', table_name='messages')
    op.drop_index('idx_messages_created_at', table_name='messages')
    op.drop_index('idx_messages_conv_created', table_name='messages')
    op.drop_index('idx_messages_conversation_id', table_name='messages')
    op.drop_index('idx_conversations_updated_at', table_name='conversations')
    op.drop_index('idx_conversations_created_at', table_name='conversations')
    
    # Drop tables
    op.drop_table('jobs')
    op.drop_table('message_embeddings')
    op.drop_table('messages')
    op.drop_table('conversations')
