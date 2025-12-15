from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import CategoryEnum


class DealPost(Base):
    __tablename__ = "deal_posts"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    source_thread_id = Column(String(100), nullable=True)
    canonical_url = Column(String(1000), nullable=False)
    title = Column(Text, nullable=False)
    author = Column(String(200), nullable=True)
    posted_at = Column(DateTime, nullable=True, index=True)
    last_seen_at = Column(DateTime, server_default=func.now(), nullable=False)
    category = Column(SQLEnum(CategoryEnum), nullable=True, index=True)
    raw_html = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    source = relationship("Source", back_populates="deal_posts")
    deal_items = relationship("DealItem", back_populates="deal_post", cascade="all, delete-orphan")
    fingerprints = relationship("DealFingerprint", back_populates="deal_post", cascade="all, delete-orphan")
