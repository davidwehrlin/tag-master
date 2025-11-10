"""create_cards_table

Revision ID: bf3c5feb0f9d
Revises: cf3985b58c55
Create Date: 2025-11-09 16:16:11.848931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'bf3c5feb0f9d'
down_revision: Union[str, None] = 'cf3985b58c55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cards table for grouping 3-6 players per round."""
    op.create_table(
        'cards',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('round_id', UUID(as_uuid=True), sa.ForeignKey('rounds.id'), nullable=False, comment='Parent round ID'),
        sa.Column('creator_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='Player who created the card'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_card_round', 'cards', ['round_id'])
    op.create_index('idx_card_creator', 'cards', ['creator_id'])


def downgrade() -> None:
    """Drop cards table and indexes."""
    op.drop_index('idx_card_creator', table_name='cards')
    op.drop_index('idx_card_round', table_name='cards')
    op.drop_table('cards')
