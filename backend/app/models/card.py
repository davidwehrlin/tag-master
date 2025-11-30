from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class Card(BaseModel, SoftDeleteMixin):
    __tablename__ = "cards"

    creator_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    creator = relationship("Player", back_populates="created_cards")
