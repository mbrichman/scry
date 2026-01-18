"""Add authentication models

Revision ID: c41d52d02da3
Revises: 17ea91610659
Create Date: 2026-01-18 15:22:55.327629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c41d52d02da3'
down_revision: Union[str, Sequence[str], None] = '17ea91610659'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add authentication tables for Flask-Security."""
    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('permissions', sa.Text(), nullable=True),
        sa.Column('update_datetime', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('fs_uniquifier', sa.String(length=64), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('current_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(length=64), nullable=True),
        sa.Column('current_login_ip', sa.String(length=64), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=True),
        sa.Column('us_totp_secrets', sa.Text(), nullable=True),
        sa.Column('us_phone_number', sa.String(length=128), nullable=True),
        sa.Column('tf_primary_method', sa.String(length=64), nullable=True),
        sa.Column('tf_totp_secret', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('fs_uniquifier')
    )

    # Create roles_users association table
    op.create_table('roles_users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Create webauthn table for passkeys
    op.create_table('webauthn',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('credential_id', sa.LargeBinary(), nullable=False),
        sa.Column('public_key', sa.LargeBinary(), nullable=False),
        sa.Column('sign_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('transports', sa.Text(), nullable=True),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('usage', sa.String(length=64), nullable=False),
        sa.Column('backup_state', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('device_type', sa.String(length=64), nullable=True),
        sa.Column('lastuse_datetime', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('credential_id')
    )
    op.create_index('idx_webauthn_user_id', 'webauthn', ['user_id'])


def downgrade() -> None:
    """Downgrade schema - Remove authentication tables."""
    op.drop_index('idx_webauthn_user_id', table_name='webauthn')
    op.drop_table('webauthn')
    op.drop_table('roles_users')
    op.drop_table('users')
    op.drop_table('roles')
