import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CategoryEnum(str, enum.Enum):
    SHARED = "shared"
    RESELLER = "reseller"
    VPS = "vps"
    DEDICATED = "dedicated"
    CLOUD = "cloud"
    COLO = "colo"
    OTHER = "other"


class BillingPeriodEnum(str, enum.Enum):
    MONTH = "month"
    YEAR = "year"
    ONE_TIME = "one_time"


class FingerprintTypeEnum(str, enum.Enum):
    STRICT = "strict"
    FUZZY = "fuzzy"
