"""create_tag_history_table

Revision ID: 13833449efaa
Revises: 5daa3893ac64
Create Date: 2025-11-09 16:20:44.290031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '13833449efaa'
down_revision: Union[str, None] = '5daa3893ac64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tag_history table for audit trail of tag assignments."""
    op.create_table(
        'tag_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('tag_number', sa.Integer, nullable=False, comment='Tag number at this point in time'),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='Player ID'),
        sa.Column('season_id', UUID(as_uuid=True), sa.ForeignKey('seasons.id'), nullable=False, comment='Season ID'),
        sa.Column('round_id', UUID(as_uuid=True), sa.ForeignKey('rounds.id'), nullable=True, comment='Round that triggered assignment (null for initial)'),
        sa.Column('assignment_date', sa.DateTime(timezone=True), nullable=False, comment='When tag was assigned'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_tag_history_player', 'tag_history', ['player_id'])
    op.create_index('idx_tag_history_season', 'tag_history', ['season_id'])
    op.create_index('idx_tag_history_round', 'tag_history', ['round_id'])
    op.create_index('idx_tag_history_player_season', 'tag_history', ['player_id', 'season_id'])
    op.create_index('idx_tag_history_assignment_date', 'tag_history', ['assignment_date'])


def downgrade() -> None:
    """Drop tag_history table and indexes."""
    op.drop_index('idx_tag_history_assignment_date', table_name='tag_history')
    op.drop_index('idx_tag_history_player_season', table_name='tag_history')
    op.drop_index('idx_tag_history_round', table_name='tag_history')
    op.drop_index('idx_tag_history_season', table_name='tag_history')
    op.drop_index('idx_tag_history_player', table_name='tag_history')
    op.drop_table('tag_history')
