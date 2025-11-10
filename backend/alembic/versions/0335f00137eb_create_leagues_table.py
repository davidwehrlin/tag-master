"""create_leagues_table

Revision ID: 0335f00137eb
Revises: 36354de73453
Create Date: 2025-11-09 16:10:36.593655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '0335f00137eb'
down_revision: Union[str, None] = '36354de73453'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create leagues table with organizer and visibility support."""
    op.create_table(
        'leagues',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('name', sa.String(255), nullable=False, comment='League name'),
        sa.Column('description', sa.Text, nullable=True, comment='League description and details'),
        sa.Column('rules', sa.Text, nullable=True, comment='League-specific rules'),
        sa.Column('visibility', sa.Enum('public', 'private', name='league_visibility'), nullable=False, server_default='public', comment='Public or private league'),
        sa.Column('organizer_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='Creator/owner player ID'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft deletion timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_league_organizer', 'leagues', ['organizer_id'])
    op.create_index('idx_league_visibility', 'leagues', ['visibility'])
    op.create_index('idx_league_deleted', 'leagues', ['deleted_at'])


def downgrade() -> None:
    """Drop leagues table and indexes."""
    op.drop_index('idx_league_deleted', table_name='leagues')
    op.drop_index('idx_league_visibility', table_name='leagues')
    op.drop_index('idx_league_organizer', table_name='leagues')
    op.drop_table('leagues')
    op.execute("DROP TYPE league_visibility")
