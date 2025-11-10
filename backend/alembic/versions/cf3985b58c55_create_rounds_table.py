"""create_rounds_table

Revision ID: cf3985b58c55
Revises: 623e8f7a14c0
Create Date: 2025-11-09 16:14:10.464565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'cf3985b58c55'
down_revision: Union[str, None] = '623e8f7a14c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create rounds table for disc golf game events."""
    op.create_table(
        'rounds',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('season_id', UUID(as_uuid=True), sa.ForeignKey('seasons.id'), nullable=False, comment='Parent season ID'),
        sa.Column('creator_id', UUID(as_uuid=True), sa.ForeignKey('players.id'), nullable=False, comment='TagMaster/Assistant who created round'),
        sa.Column('date', sa.Date, nullable=False, comment='Round date'),
        sa.Column('course_name', sa.String(255), nullable=False, comment='Course name'),
        sa.Column('location', sa.String(500), nullable=True, comment='Course location/address'),
        sa.Column('start_time', sa.Time, nullable=True, comment='Scheduled start time'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft deletion timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_round_season', 'rounds', ['season_id'])
    op.create_index('idx_round_date', 'rounds', ['date'])
    op.create_index('idx_round_deleted', 'rounds', ['deleted_at'])


def downgrade() -> None:
    """Drop rounds table and indexes."""
    op.drop_index('idx_round_deleted', table_name='rounds')
    op.drop_index('idx_round_date', table_name='rounds')
    op.drop_index('idx_round_season', table_name='rounds')
    op.drop_table('rounds')
