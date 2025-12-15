from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import FingerprintTypeEnum


class DealFingerprint(Base):
    __tablename__ = "deal_fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    deal_post_id = Column(Integer, ForeignKey("deal_posts.id", ondelete="CASCADE"), nullable=False)
    fingerprint = Column(String(64), nullable=False, index=True)
    fingerprint_type = Column(SQLEnum(FingerprintTypeEnum), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    deal_post = relationship("DealPost", back_populates="fingerprints")
