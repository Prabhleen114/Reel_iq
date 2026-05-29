"""ReelIQ — AI Insights Routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Reel
from app.schemas import (
    CaptionImproveRequest, CaptionImproveResponse,
    HookScoreRequest, HookScoreResponse,
    HashtagsResponse, PostingTimesResponse, ViralPatternsResponse,
)
from app.routes.auth import get_current_user
from app.ai_client import call_groq_async, parse_json_response
from app.prompts.hook_score_prompt import build_hook_score_prompt
from app.prompts.caption_improve_prompt import build_caption_improve_prompt

router = APIRouter(prefix="/insights", tags=["AI Insights"])


@router.get("/hashtags", response_model=HashtagsResponse)
async def get_best_hashtags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Reel).where(Reel.user_id == current_user.id).order_by(Reel.views.desc()).limit(20)
    )
    reels = result.scalars().all()

    hashtag_perf = {}
    for reel in reels:
        for tag in (reel.hashtags or []):
            if tag not in hashtag_perf:
                hashtag_perf[tag] = {"views": [], "count": 0}
            hashtag_perf[tag]["views"].append(reel.views)
            hashtag_perf[tag]["count"] += 1

    hashtags = []
    for tag, data in sorted(hashtag_perf.items(), key=lambda x: sum(x[1]["views"]) / len(x[1]["views"]), reverse=True)[:30]:
        avg_reach = sum(data["views"]) // len(data["views"]) if data["views"] else 0
        hashtags.append({"tag": tag, "avg_reach": avg_reach, "usage_count": data["count"]})

    niche = "general"
    if reels and reels[0].niche_tags:
        niche = reels[0].niche_tags[0]

    return HashtagsResponse(hashtags=hashtags, niche=niche)


@router.get("/posting-times", response_model=PostingTimesResponse)
async def get_posting_times(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Reel).where(Reel.user_id == current_user.id, Reel.posted_at.isnot(None))
    )
    reels = result.scalars().all()

    time_perf = {}
    for reel in reels:
        if reel.posted_at:
            key = f"{reel.posted_at.strftime('%A')}-{reel.posted_at.hour}"
            if key not in time_perf:
                time_perf[key] = {"day": reel.posted_at.strftime("%A"), "hour": reel.posted_at.hour, "engagement": []}
            eng = reel.likes + reel.comments + reel.saves + reel.shares
            time_perf[key]["engagement"].append(eng)

    best_times = []
    for key, data in sorted(time_perf.items(), key=lambda x: sum(x[1]["engagement"]) / max(len(x[1]["engagement"]), 1), reverse=True)[:10]:
        avg_eng = sum(data["engagement"]) // max(len(data["engagement"]), 1)
        best_times.append({"day": data["day"], "hour": data["hour"], "avg_engagement": avg_eng})

    return PostingTimesResponse(best_times=best_times, timezone="UTC")


@router.get("/viral-patterns", response_model=ViralPatternsResponse)
async def get_viral_patterns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Reel).where(Reel.user_id == current_user.id).order_by(Reel.views.desc()).limit(50)
    )
    reels = result.scalars().all()

    if not reels:
        return ViralPatternsResponse(patterns=[], top_traits=[])

    avg_views = sum(r.views for r in reels) / len(reels) if reels else 0
    top_reels = [r for r in reels if r.views > avg_views * 1.5]

    patterns = []
    traits = set()

    for reel in top_reels[:10]:
        caption = reel.caption or ""
        pattern = {"views": reel.views, "traits": []}
        if len(caption) < 100:
            pattern["traits"].append("short_caption")
            traits.add("Short captions")
        if "?" in caption:
            pattern["traits"].append("question_hook")
            traits.add("Question hooks")
        if any(c.isdigit() for c in caption[:50]):
            pattern["traits"].append("number_hook")
            traits.add("Number-based hooks")
        if len(reel.hashtags or []) > 10:
            pattern["traits"].append("heavy_hashtags")
            traits.add("10+ hashtags")
        patterns.append(pattern)

    return ViralPatternsResponse(patterns=patterns, top_traits=list(traits))


@router.post("/caption", response_model=CaptionImproveResponse)
async def improve_caption(
    request: CaptionImproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    top_captions = request.top_captions
    if not top_captions:
        result = await db.execute(
            select(Reel.caption).where(Reel.user_id == current_user.id).order_by(Reel.views.desc()).limit(5)
        )
        top_captions = [r[0] for r in result.all() if r[0]]

    prompt = build_caption_improve_prompt(request.caption, request.niche, top_captions)
    result_text = await call_groq_async(prompt)
    result = parse_json_response(result_text)

    return CaptionImproveResponse(
        improved_caption=result.get("improved_caption", request.caption),
        cta_added=result.get("cta_added", ""),
        hashtags=result.get("hashtags", []),
        tone=result.get("tone", ""),
        why_better=result.get("why_better", ""),
    )


@router.post("/hook-score", response_model=HookScoreResponse)
async def score_hook(request: HookScoreRequest):
    prompt = build_hook_score_prompt(request.hook, request.niche)
    result_text = await call_groq_async(prompt)
    result = parse_json_response(result_text)

    return HookScoreResponse(
        score=result.get("score", 0),
        verdict=result.get("verdict", ""),
        why_it_works_or_fails=result.get("why_it_works_or_fails", ""),
        improved_versions=result.get("improved_versions", []),
        psychology_trigger_used=result.get("psychology_trigger_used", ""),
    )
