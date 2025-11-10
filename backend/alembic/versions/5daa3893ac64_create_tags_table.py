"""create_tags_table

Revision ID: 5daa3893ac64
Revises: 481970681d86
Create Date: 2025-11-09 16:19:35.682580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '5daa3893ac64'
down_revision: Union[str, None] = '481970681d86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tags table for current player rankings within seasons."""
    op.create_table(
        'tags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='Player ID'),
        sa.Column('season_id', UUID(as_uuid=True), sa.ForeignKey('seasons.id'), nullable=False, comment='Season ID'),
        sa.Column('tag_number', sa.Integer, nullable=False, comment='Tag position (1 is best)'),
        sa.Column('assignment_date', sa.DateTime(timezone=True), nullable=False, comment='When tag was assigned/updated'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create unique constraints and indexes
    op.create_unique_constraint('uq_tag_player_season', 'tags', ['player_id', 'season_id'])
    op.create_unique_constraint('uq_tag_season_number', 'tags', ['season_id', 'tag_number'])
    op.create_index('idx_tag_player', 'tags', ['player_id'])
    op.create_index('idx_tag_season', 'tags', ['season_id'])
    op.create_index('idx_tag_season_number', 'tags', ['season_id', 'tag_number'])


def downgrade() -> None:
    """Drop tags table and indexes."""
    op.drop_index('idx_tag_season_number', table_name='tags')
    op.drop_index('idx_tag_season', table_name='tags')
    op.drop_index('idx_tag_player', table_name='tags')
    op.drop_constraint('uq_tag_season_number', 'tags', type_='unique')
    op.drop_constraint('uq_tag_player_season', 'tags', type_='unique')
    op.drop_table('tags')
