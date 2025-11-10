"""create_participations_table

Revision ID: 270c7d72b603
Revises: bf3c5feb0f9d
Create Date: 2025-11-09 16:17:25.328345

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '270c7d72b603'
down_revision: Union[str, None] = 'bf3c5feb0f9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create participations table with score tracking and confirmation workflow."""
    op.create_table(
        'participations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='Player ID'),
        sa.Column('round_id', UUID(as_uuid=True), sa.ForeignKey('rounds.id'), nullable=False, comment='Round ID'),
        sa.Column('card_id', UUID(as_uuid=True), sa.ForeignKey('cards.id'), nullable=True, comment='Card ID (assigned after physical checkin)'),
        sa.Column('status', sa.Enum('registered', 'checked_in', 'completed', 'dnf', name='participation_status'), nullable=False, server_default='registered', comment='Participation status'),
        sa.Column('online_registration_time', sa.DateTime(timezone=True), nullable=True, comment='Online pre-registration timestamp'),
        sa.Column('physical_checkin_time', sa.DateTime(timezone=True), nullable=True, comment='Physical check-in timestamp'),
        sa.Column('score', sa.Integer, nullable=True, comment='Stroke count (lower is better)'),
        sa.Column('score_entered_by_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=True, comment='Who entered the score'),
        sa.Column('score_entered_at', sa.DateTime(timezone=True), nullable=True, comment='When score was entered'),
        sa.Column('score_confirmed', sa.Boolean, nullable=False, server_default='false', comment='Score confirmation status'),
        sa.Column('score_confirmed_by_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=True, comment='Who confirmed the score'),
        sa.Column('score_confirmed_at', sa.DateTime(timezone=True), nullable=True, comment='When score was confirmed'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create unique constraint and indexes
    op.create_unique_constraint('uq_participation_player_round', 'participations', ['player_id', 'round_id'])
    op.create_index('idx_participation_player', 'participations', ['player_id'])
    op.create_index('idx_participation_round', 'participations', ['round_id'])
    op.create_index('idx_participation_card', 'participations', ['card_id'])
    op.create_index('idx_participation_status', 'participations', ['status'])


def downgrade() -> None:
    """Drop participations table and indexes."""
    op.drop_index('idx_participation_status', table_name='participations')
    op.drop_index('idx_participation_card', table_name='participations')
    op.drop_index('idx_participation_round', table_name='participations')
    op.drop_index('idx_participation_player', table_name='participations')
    op.drop_constraint('uq_participation_player_round', 'participations', type_='unique')
    op.drop_table('participations')
    op.execute("DROP TYPE participation_status")
