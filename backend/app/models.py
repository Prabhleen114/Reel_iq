"""ReelIQ Backend — SQLAlchemy Models (Complete Database Schema)"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, DateTime,
    ForeignKey, JSON, Enum, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    avatar = Column(Text, nullable=True)
    instagram_id = Column(String(100), nullable=True, unique=True)
    plan = Column(String(20), default="elite")
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    instagram_accounts = relationship("InstagramAccount", back_populates="user", cascade="all, delete-orphan")
    reels = relationship("Reel", back_populates="user", cascade="all, delete-orphan")
    video_analyses = relationship("VideoAnalysis", back_populates="user", cascade="all, delete-orphan")
    content_calendar = relationship("ContentCalendar", back_populates="user", cascade="all, delete-orphan")
    ab_tests = relationship("ABTest", back_populates="user", cascade="all, delete-orphan")
    competitor_analyses = relationship("CompetitorAnalysis", back_populates="user", cascade="all, delete-orphan")


class InstagramAccount(Base):
    __tablename__ = "instagram_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(Text, nullable=False)
    username = Column(String(100), nullable=False)
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    media_count = Column(Integer, default=0)
    biography = Column(Text, nullable=True)
    profile_picture_url = Column(Text, nullable=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    token_expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="instagram_accounts")

    __table_args__ = (
        Index("ix_instagram_accounts_user_id", "user_id"),
    )


class Reel(Base):
    __tablename__ = "reels"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    instagram_reel_id = Column(String(100), nullable=True, unique=True)
    url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, default=list)
    duration = Column(Float, nullable=True)
    audio_name = Column(String(255), nullable=True)
    posted_at = Column(DateTime, nullable=True)

    # Metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)

    # AI Scores
    hook_score = Column(Float, nullable=True)
    retention_score = Column(Float, nullable=True)
    viral_score = Column(Float, nullable=True)

    # Tags & Analysis
    niche_tags = Column(JSON, default=list)
    analysis_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reels")
    video_analyses = relationship("VideoAnalysis", back_populates="reel", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_reels_user_id", "user_id"),
        Index("ix_reels_posted_at", "posted_at"),
        Index("ix_reels_viral_score", "viral_score"),
    )


class VideoAnalysis(Base):
    __tablename__ = "video_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reel_id = Column(String(36), ForeignKey("reels.id", ondelete="SET NULL"), nullable=True)
    video_url = Column(Text, nullable=True)
    video_key = Column(String(500), nullable=True)  # S3 key

    # Analysis Results
    hook_score = Column(Float, nullable=True)
    drop_off_points = Column(JSON, default=list)  # [{timestamp, reason}]
    cut_suggestions = Column(JSON, default=list)  # [{start, end, reason}]
    hook_rewrites = Column(JSON, default=list)  # [string x3]
    viral_score = Column(Float, nullable=True)
    engagement_probability = Column(Float, nullable=True)
    rewrite_caption = Column(Text, nullable=True)
    rewrite_structure = Column(JSON, nullable=True)
    pacing_verdict = Column(Text, nullable=True)
    visual_engagement = Column(Float, nullable=True)
    hook_analysis = Column(Text, nullable=True)
    viral_optimizations = Column(JSON, default=list)
    move_earlier_suggestions = Column(JSON, default=list)

    # Video Metadata
    duration = Column(Float, nullable=True)
    resolution = Column(String(20), nullable=True)
    fps = Column(Float, nullable=True)
    frame_count = Column(Integer, nullable=True)

    # Processing
    status = Column(String(20), default="pending")  # pending, processing, analyzing, completed, failed
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="video_analyses")
    reel = relationship("Reel", back_populates="video_analyses")

    __table_args__ = (
        Index("ix_video_analyses_user_id", "user_id"),
        Index("ix_video_analyses_status", "status"),
    )


class ContentCalendar(Base):
    __tablename__ = "content_calendar"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    hook = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, default=list)
    format = Column(String(50), nullable=True)  # reel, carousel, story, etc.
    niche = Column(String(100), nullable=True)
    status = Column(String(20), default="planned")  # planned, draft, published, skipped
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="content_calendar")

    __table_args__ = (
        Index("ix_content_calendar_user_id_date", "user_id", "date"),
    )


class ABTest(Base):
    __tablename__ = "ab_tests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hook_a = Column(Text, nullable=False)
    hook_b = Column(Text, nullable=False)
    niche = Column(String(100), nullable=True)
    predicted_score_a = Column(Float, nullable=True)
    predicted_score_b = Column(Float, nullable=True)
    analysis_a = Column(JSON, nullable=True)
    analysis_b = Column(JSON, nullable=True)
    winner = Column(String(1), nullable=True)  # "a" or "b"
    verdict = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ab_tests")

    __table_args__ = (
        Index("ix_ab_tests_user_id", "user_id"),
    )


class CompetitorAnalysis(Base):
    __tablename__ = "competitor_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    competitor_username = Column(String(100), nullable=False)
    analysis_json = Column(JSON, nullable=True)
    their_strengths = Column(JSON, default=list)
    their_weaknesses = Column(JSON, default=list)
    content_gaps = Column(JSON, default=list)
    hook_styles = Column(JSON, default=list)
    steal_ideas = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="competitor_analyses")

    __table_args__ = (
        Index("ix_competitor_analyses_user_id", "user_id"),
    )
