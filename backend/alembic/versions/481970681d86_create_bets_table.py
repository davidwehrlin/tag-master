"""create_bets_table

Revision ID: 481970681d86
Revises: 270c7d72b603
Create Date: 2025-11-09 16:18:28.147866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, NUMERIC


# revision identifiers, used by Alembic.
revision: str = '481970681d86'
down_revision: Union[str, None] = '270c7d72b603'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create bets table for optional money bets/challenges during rounds."""
    op.create_table(
        'bets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='Player ID'),
        sa.Column('round_id', UUID(as_uuid=True), sa.ForeignKey('rounds.id'), nullable=False, comment='Round ID'),
        sa.Column('bet_type', sa.Enum('ace_pot', 'ctp', 'challenge', name='bet_type'), nullable=False, comment='Bet type (ace_pot, ctp, challenge)'),
        sa.Column('amount', NUMERIC(10, 2), nullable=False, comment='Bet amount (currency)'),
        sa.Column('description', sa.String(500), nullable=True, comment='Optional bet description'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_bet_player', 'bets', ['player_id'])
    op.create_index('idx_bet_round', 'bets', ['round_id'])
    op.create_index('idx_bet_type', 'bets', ['bet_type'])


def downgrade() -> None:
    """Drop bets table and indexes."""
    op.drop_index('idx_bet_type', table_name='bets')
    op.drop_index('idx_bet_round', table_name='bets')
    op.drop_index('idx_bet_player', table_name='bets')
    op.drop_table('bets')
    op.execute("DROP TYPE bet_type")
