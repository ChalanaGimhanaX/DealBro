from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import BillingPeriodEnum


class DealItem(Base):
    __tablename__ = "deal_items"

    id = Column(Integer, primary_key=True, index=True)
    deal_post_id = Column(Integer, ForeignKey("deal_posts.id", ondelete="CASCADE"), nullable=False)
    provider_name = Column(String(200), nullable=True)
    provider_domain = Column(String(200), nullable=True, index=True)
    price_amount = Column(Numeric(10, 2), nullable=True)
    price_currency = Column(String(3), nullable=True, index=True)
    billing_period = Column(SQLEnum(BillingPeriodEnum), nullable=True, index=True)
    price_monthly_normalized = Column(Numeric(10, 2), nullable=True, index=True)
    location = Column(String(200), nullable=True)
    cpu = Column(String(100), nullable=True)
    ram_mb = Column(Integer, nullable=True)
    storage_gb = Column(Integer, nullable=True)
    bandwidth_gb = Column(Integer, nullable=True)
    order_url = Column(String(1000), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    deal_post = relationship("DealPost", back_populates="deal_items")
