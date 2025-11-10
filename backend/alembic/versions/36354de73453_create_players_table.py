"""create_players_table

Revision ID: 36354de73453
Revises: 
Create Date: 2025-11-09 16:08:22.089214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY


# revision identifiers, used by Alembic.
revision: str = '36354de73453'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create players table with authentication and soft delete support."""
    op.create_table(
        'players',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('email', sa.String(255), nullable=False, unique=True, comment='Login email address'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='Bcrypt hashed password'),
        sa.Column('name', sa.String(255), nullable=False, comment='Player display name'),
        sa.Column('bio', sa.String(1000), nullable=True, comment='Optional player biography'),
        sa.Column('roles', ARRAY(sa.String), nullable=False, server_default='{"Player"}', comment='Array of role names'),
        sa.Column('email_verified', sa.Boolean, nullable=False, server_default='false', comment='Email verification status'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft deletion timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_player_email', 'players', ['email'])
    op.create_index('idx_player_deleted', 'players', ['deleted_at'])


def downgrade() -> None:
    """Drop players table and indexes."""
    op.drop_index('idx_player_deleted', table_name='players')
    op.drop_index('idx_player_email', table_name='players')
    op.drop_table('players')
