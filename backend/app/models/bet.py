from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class Bet(BaseModel, SoftDeleteMixin):
    __tablename__ = "bets"

    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    player = relationship("Player", back_populates="bets")
