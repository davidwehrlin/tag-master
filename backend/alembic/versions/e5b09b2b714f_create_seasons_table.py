"""create_seasons_table

Revision ID: e5b09b2b714f
Revises: 0335f00137eb
Create Date: 2025-11-09 16:12:24.508426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e5b09b2b714f'
down_revision: Union[str, None] = '0335f00137eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create seasons table with date range and registration period support."""
    op.create_table(
        'seasons',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='Unique identifier'),
        sa.Column('name', sa.String(255), nullable=False, comment='Season name (e.g., "Spring 2025")'),
        sa.Column('league_id', UUID(as_uuid=True), sa.ForeignKey('leagues.id'), nullable=False, comment='Parent league ID'),
        sa.Column('start_date', sa.Date, nullable=False, comment='Season start date'),
        sa.Column('end_date', sa.Date, nullable=False, comment='Season end date'),
        sa.Column('registration_open_date', sa.Date, nullable=True, comment='Registration opens (optional)'),
        sa.Column('registration_close_date', sa.Date, nullable=True, comment='Registration closes (optional)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record last update timestamp'),
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_season_league', 'seasons', ['league_id'])
    op.create_index('idx_season_dates', 'seasons', ['start_date', 'end_date'])


def downgrade() -> None:
    """Drop seasons table and indexes."""
    op.drop_index('idx_season_dates', table_name='seasons')
    op.drop_index('idx_season_league', table_name='seasons')
    op.drop_table('seasons')
