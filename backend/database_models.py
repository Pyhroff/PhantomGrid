from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import DateTime

from sqlalchemy.orm import declarative_base

from datetime import datetime

Base = declarative_base()


class UserProfile(Base):

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)

    user_id = Column(String, unique=True)

    layer1_vectors = Column(String)

    layer2_vectors = Column(String)

    pin_vectors = Column(String)

    # Layer-API baselines (separate feature space from the unified /enroll endpoint)
    l1_baseline = Column(String)   # JSON list of [decoy_interactions, hover_ms, latency_ms]
    l2_baseline = Column(String)   # JSON list of [nav_entropy, digit_fluency_ms, bene_dwell_ms]
    l3_baseline = Column(String)   # JSON list of interval lists


class SessionLog(Base):

    __tablename__ = "session_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id = Column(
        String,
        unique=True,
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    user_id = Column(
        String,
        nullable=False
    )

    layer1_score = Column(
        Float,
        default=0
    )

    layer2_score = Column(
        Float,
        default=0
    )

    layer3_score = Column(
        Float,
        default=0
    )

    composite_score = Column(
        Float,
        default=0
    )

    decision = Column(
        String,
        nullable=False
    )

    # Tamper-evident audit chain (Person 3)
    row_hash = Column(String)

    prev_hash = Column(String)