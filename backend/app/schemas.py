"""ReelIQ Backend — Pydantic Schemas for Request/Response Validation"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime


# ═══════════════════════════════════════════════
# Auth Schemas
# ═══════════════════════════════════════════════
class UserCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    name: Optional[str] = None
    password: Optional[str] = None


class InstagramRegisterRequest(BaseModel):
    instagram_username: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    instagram_id: Optional[str] = None
    plan: str = "elite"
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class InstagramConnectRequest(BaseModel):
    code: str


class InstagramCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


# ═══════════════════════════════════════════════
# Instagram Schemas
# ═══════════════════════════════════════════════
class InstagramAccountResponse(BaseModel):
    id: str
    username: str
    followers: int
    following: int
    media_count: int
    biography: Optional[str] = None
    profile_picture_url: Optional[str] = None
    connected_at: datetime

    class Config:
        from_attributes = True


class ReelResponse(BaseModel):
    id: str
    instagram_reel_id: Optional[str] = None
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    hashtags: List[str] = []
    duration: Optional[float] = None
    audio_name: Optional[str] = None
    posted_at: Optional[datetime] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    hook_score: Optional[float] = None
    retention_score: Optional[float] = None
    viral_score: Optional[float] = None
    niche_tags: List[str] = []
    analysis_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ReelListResponse(BaseModel):
    reels: List[ReelResponse]
    total: int
    page: int
    per_page: int


class ImportRequest(BaseModel):
    data: Dict[str, Any]


# ═══════════════════════════════════════════════
# Analysis Schemas
# ═══════════════════════════════════════════════
class VideoAnalysisResponse(BaseModel):
    id: str
    reel_id: Optional[str] = None
    video_url: Optional[str] = None
    hook_score: Optional[float] = None
    drop_off_points: List[Dict[str, Any]] = []
    cut_suggestions: List[Dict[str, Any]] = []
    hook_rewrites: List[str] = []
    viral_score: Optional[float] = None
    engagement_probability: Optional[float] = None
    rewrite_caption: Optional[str] = None
    rewrite_structure: Optional[Dict[str, Any]] = None
    pacing_verdict: Optional[str] = None
    visual_engagement: Optional[float] = None
    hook_analysis: Optional[str] = None
    viral_optimizations: List[str] = []
    move_earlier_suggestions: List[Dict[str, Any]] = []
    duration: Optional[float] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    status: str = "pending"
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════
# AI Insights Schemas
# ═══════════════════════════════════════════════
class CaptionImproveRequest(BaseModel):
    caption: str
    niche: Optional[str] = None
    top_captions: Optional[List[str]] = None


class CaptionImproveResponse(BaseModel):
    improved_caption: str
    cta_added: str
    hashtags: List[str]
    tone: str
    why_better: str


class HookScoreRequest(BaseModel):
    hook: str
    niche: Optional[str] = None


class HookScoreResponse(BaseModel):
    score: float
    verdict: str
    why_it_works_or_fails: str
    improved_versions: List[str]
    psychology_trigger_used: str


class HashtagsResponse(BaseModel):
    hashtags: List[Dict[str, Any]]
    niche: str


class PostingTimesResponse(BaseModel):
    best_times: List[Dict[str, Any]]
    timezone: str


class ViralPatternsResponse(BaseModel):
    patterns: List[Dict[str, Any]]
    top_traits: List[str]


# ═══════════════════════════════════════════════
# Content Lab Schemas
# ═══════════════════════════════════════════════
class ViralScoreRequest(BaseModel):
    hook: str
    caption: str
    niche: Optional[str] = None
    hashtags: Optional[List[str]] = None


class ViralScoreResponse(BaseModel):
    viral_score: float
    confidence: str
    key_signals: List[Dict[str, Any]]
    missing_elements: List[str]
    predicted_reach_multiplier: float


class ABTestRequest(BaseModel):
    hook_a: str
    hook_b: str
    niche: Optional[str] = None


class ABTestResponse(BaseModel):
    id: str
    hook_a: str
    hook_b: str
    predicted_score_a: float
    predicted_score_b: float
    winner: str
    verdict: str
    analysis_a: Dict[str, Any]
    analysis_b: Dict[str, Any]


class ReelRewriteRequest(BaseModel):
    hook: Optional[str] = None
    caption: Optional[str] = None
    video_analysis_id: Optional[str] = None
    niche: Optional[str] = None


class ReelRewriteResponse(BaseModel):
    new_hook: str
    hook_psychology: str
    new_caption: str
    new_structure: List[Dict[str, Any]]
    viral_potential_after: float
    what_changed: str


# ═══════════════════════════════════════════════
# Strategy Schemas
# ═══════════════════════════════════════════════
class ContentCalendarResponse(BaseModel):
    id: str
    date: datetime
    hook: Optional[str] = None
    caption: Optional[str] = None
    hashtags: List[str] = []
    format: Optional[str] = None
    niche: Optional[str] = None
    status: str = "planned"

    class Config:
        from_attributes = True


class ContentCalendarListResponse(BaseModel):
    items: List[ContentCalendarResponse]
    total: int


class HookBankResponse(BaseModel):
    hooks: List[Dict[str, Any]]
    niche: str


class ContentIdeasResponse(BaseModel):
    ideas: List[Dict[str, Any]]
    trending_topics: List[str]


# ═══════════════════════════════════════════════
# Competitor Schemas
# ═══════════════════════════════════════════════
class CompetitorAnalyzeRequest(BaseModel):
    competitor_username: str
    their_posts: Optional[List[Dict[str, Any]]] = None


class CompetitorAnalysisResponse(BaseModel):
    id: str
    competitor_username: str
    their_strengths: List[str]
    their_weaknesses: List[str]
    content_gaps: List[str]
    hook_styles: List[str]
    steal_ideas: List[str]
    analysis_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
# Voiceover Schemas
# ═══════════════════════════════════════════════
class VoiceoverRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "coqui-professional"
    stability: Optional[float] = 0.5
    similarity_boost: Optional[float] = 0.75


class VoiceoverResponse(BaseModel):
    audio_url: str
    duration: Optional[float] = None
    characters_used: int


# ═══════════════════════════════════════════════
# Account Analysis Schemas
# ═══════════════════════════════════════════════
class AccountAnalysisResponse(BaseModel):
    strengths: List[Dict[str, Any]]
    weaknesses: List[Dict[str, Any]]
    niche: str
    content_categories: List[Dict[str, Any]]
    viral_patterns: List[Dict[str, Any]]
    best_posting_times: List[Dict[str, Any]]
    top_hashtags: List[Dict[str, Any]]
    repetition_flags: List[str]
    growth_trajectory: str
