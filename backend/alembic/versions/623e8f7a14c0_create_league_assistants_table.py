"""create_league_assistants_table

Revision ID: 623e8f7a14c0
Revises: e5b09b2b714f
Create Date: 2025-11-09 16:13:37.767614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '623e8f7a14c0'
down_revision: Union[str, None] = 'e5b09b2b714f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create league_assistants table for league-specific assistant role assignments."""
    op.create_table(
        'league_assistants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='Assistant player ID'),
        sa.Column('league_id', UUID(as_uuid=True), sa.ForeignKey('leagues.id'), nullable=False, comment='League ID'),
        sa.Column('assigned_by_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='TagMaster who assigned this assistant'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create unique constraint and indexes
    op.create_unique_constraint('uq_league_assistant', 'league_assistants', ['player_id', 'league_id'])
    op.create_index('idx_assistant_player', 'league_assistants', ['player_id'])
    op.create_index('idx_assistant_league', 'league_assistants', ['league_id'])


def downgrade() -> None:
    """Drop league_assistants table and indexes."""
    op.drop_index('idx_assistant_league', table_name='league_assistants')
    op.drop_index('idx_assistant_player', table_name='league_assistants')
    op.drop_constraint('uq_league_assistant', 'league_assistants', type_='unique')
    op.drop_table('league_assistants')
