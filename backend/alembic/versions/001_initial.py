"""Initial schema — all tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-05-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("avatar", sa.Text, nullable=True),
        sa.Column("instagram_id", sa.String(100), unique=True, nullable=True),
        sa.Column("plan", sa.String(20), server_default="elite"),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # Instagram Accounts
    op.create_table(
        "instagram_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("access_token", sa.Text, nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("followers", sa.Integer, server_default="0"),
        sa.Column("following", sa.Integer, server_default="0"),
        sa.Column("media_count", sa.Integer, server_default="0"),
        sa.Column("biography", sa.Text, nullable=True),
        sa.Column("profile_picture_url", sa.Text, nullable=True),
        sa.Column("connected_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("token_expires_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_instagram_accounts_user_id", "instagram_accounts", ["user_id"])

    # Reels
    op.create_table(
        "reels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instagram_reel_id", sa.String(100), unique=True, nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("hashtags", sa.JSON, server_default="[]"),
        sa.Column("duration", sa.Float, nullable=True),
        sa.Column("audio_name", sa.String(255), nullable=True),
        sa.Column("posted_at", sa.DateTime, nullable=True),
        sa.Column("views", sa.Integer, server_default="0"),
        sa.Column("likes", sa.Integer, server_default="0"),
        sa.Column("comments", sa.Integer, server_default="0"),
        sa.Column("shares", sa.Integer, server_default="0"),
        sa.Column("saves", sa.Integer, server_default="0"),
        sa.Column("hook_score", sa.Float, nullable=True),
        sa.Column("retention_score", sa.Float, nullable=True),
        sa.Column("viral_score", sa.Float, nullable=True),
        sa.Column("niche_tags", sa.JSON, server_default="[]"),
        sa.Column("analysis_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_reels_user_id", "reels", ["user_id"])
    op.create_index("ix_reels_posted_at", "reels", ["posted_at"])
    op.create_index("ix_reels_viral_score", "reels", ["viral_score"])

    # Video Analyses
    op.create_table(
        "video_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reel_id", sa.String(36), sa.ForeignKey("reels.id", ondelete="SET NULL"), nullable=True),
        sa.Column("video_url", sa.Text, nullable=True),
        sa.Column("video_key", sa.String(500), nullable=True),
        sa.Column("hook_score", sa.Float, nullable=True),
        sa.Column("drop_off_points", sa.JSON, server_default="[]"),
        sa.Column("cut_suggestions", sa.JSON, server_default="[]"),
        sa.Column("hook_rewrites", sa.JSON, server_default="[]"),
        sa.Column("viral_score", sa.Float, nullable=True),
        sa.Column("engagement_probability", sa.Float, nullable=True),
        sa.Column("rewrite_caption", sa.Text, nullable=True),
        sa.Column("rewrite_structure", sa.JSON, nullable=True),
        sa.Column("pacing_verdict", sa.Text, nullable=True),
        sa.Column("visual_engagement", sa.Float, nullable=True),
        sa.Column("hook_analysis", sa.Text, nullable=True),
        sa.Column("viral_optimizations", sa.JSON, server_default="[]"),
        sa.Column("move_earlier_suggestions", sa.JSON, server_default="[]"),
        sa.Column("duration", sa.Float, nullable=True),
        sa.Column("resolution", sa.String(20), nullable=True),
        sa.Column("fps", sa.Float, nullable=True),
        sa.Column("frame_count", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_video_analyses_user_id", "video_analyses", ["user_id"])
    op.create_index("ix_video_analyses_status", "video_analyses", ["status"])

    # Content Calendar
    op.create_table(
        "content_calendar",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.DateTime, nullable=False),
        sa.Column("hook", sa.Text, nullable=True),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("hashtags", sa.JSON, server_default="[]"),
        sa.Column("format", sa.String(50), nullable=True),
        sa.Column("niche", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), server_default="planned"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_content_calendar_user_id_date", "content_calendar", ["user_id", "date"])

    # A/B Tests
    op.create_table(
        "ab_tests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hook_a", sa.Text, nullable=False),
        sa.Column("hook_b", sa.Text, nullable=False),
        sa.Column("niche", sa.String(100), nullable=True),
        sa.Column("predicted_score_a", sa.Float, nullable=True),
        sa.Column("predicted_score_b", sa.Float, nullable=True),
        sa.Column("analysis_a", sa.JSON, nullable=True),
        sa.Column("analysis_b", sa.JSON, nullable=True),
        sa.Column("winner", sa.String(1), nullable=True),
        sa.Column("verdict", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_ab_tests_user_id", "ab_tests", ["user_id"])

    # Competitor Analyses
    op.create_table(
        "competitor_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("competitor_username", sa.String(100), nullable=False),
        sa.Column("analysis_json", sa.JSON, nullable=True),
        sa.Column("their_strengths", sa.JSON, server_default="[]"),
        sa.Column("their_weaknesses", sa.JSON, server_default="[]"),
        sa.Column("content_gaps", sa.JSON, server_default="[]"),
        sa.Column("hook_styles", sa.JSON, server_default="[]"),
        sa.Column("steal_ideas", sa.JSON, server_default="[]"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_competitor_analyses_user_id", "competitor_analyses", ["user_id"])


def downgrade() -> None:
    op.drop_table("competitor_analyses")
    op.drop_table("ab_tests")
    op.drop_table("content_calendar")
    op.drop_table("video_analyses")
    op.drop_table("reels")
    op.drop_table("instagram_accounts")
    op.drop_table("users")
