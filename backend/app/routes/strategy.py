"""ReelIQ — Strategy Routes (Calendar, Hook Bank, Ideas)"""
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, Reel, ContentCalendar
from app.schemas import (
    ContentCalendarListResponse, ContentCalendarResponse,
    HookBankResponse, ContentIdeasResponse,
)
from app.routes.auth import get_current_user
from app.ai_client import call_groq_async, parse_json_response

router = APIRouter(prefix="/strategy", tags=["Strategy"])


@router.get("/calendar", response_model=ContentCalendarListResponse)
async def get_content_calendar(
    weeks: int = Query(1, ge=1, le=4),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ContentCalendar)
        .where(ContentCalendar.user_id == current_user.id)
        .order_by(ContentCalendar.date.asc())
    )
    items = result.scalars().all()

    if not items:
        # Auto-generate calendar using AI
        reels_result = await db.execute(
            select(Reel).where(Reel.user_id == current_user.id).order_by(Reel.views.desc()).limit(10)
        )
        top_reels = reels_result.scalars().all()

        context = "No existing reels."
        if top_reels:
            context = json.dumps([{
                "caption": r.caption[:100] if r.caption else "",
                "views": r.views,
                "likes": r.likes,
                "hashtags": (r.hashtags or [])[:5],
            } for r in top_reels], default=str)

        prompt = f"""Generate a {weeks}-week Instagram content calendar. This creator's top performing content:
{context}

For each day (Mon-Sun, {weeks} weeks starting from tomorrow), create one reel idea.

Return ONLY this JSON:
{{
    "calendar": [
        {{
            "date": "YYYY-MM-DD",
            "hook": "The opening hook text",
            "caption": "Full caption with CTA",
            "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
            "format": "reel|carousel|story",
            "niche": "content niche"
        }}
    ]
}}"""

        result_text = await call_groq_async(prompt, max_tokens=6000)
        result_data = parse_json_response(result_text)

        calendar_items = result_data.get("calendar", [])
        for item in calendar_items:
            try:
                date = datetime.strptime(item["date"], "%Y-%m-%d")
            except (ValueError, KeyError):
                date = datetime.utcnow() + timedelta(days=len(items))

            cal_entry = ContentCalendar(
                user_id=current_user.id,
                date=date,
                hook=item.get("hook", ""),
                caption=item.get("caption", ""),
                hashtags=item.get("hashtags", []),
                format=item.get("format", "reel"),
                niche=item.get("niche", ""),
                status="planned",
            )
            db.add(cal_entry)
            items.append(cal_entry)

    return ContentCalendarListResponse(
        items=[ContentCalendarResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.get("/hook-bank", response_model=HookBankResponse)
async def get_hook_bank(
    niche: str = Query("general"),
    current_user: User = Depends(get_current_user),
):
    prompt = f"""Generate 20 high-performing Instagram Reel hooks for the "{niche}" niche.

Each hook should use a different hook archetype (question, bold claim, story, POV, "This is your sign", list, controversy, etc.)

Return ONLY this JSON:
{{
    "hooks": [
        {{
            "hook": "The hook text",
            "archetype": "Hook style name",
            "psychology": "Why this works",
            "estimated_score": 0-100
        }}
    ]
}}"""

    result_text = await call_groq_async(prompt, max_tokens=4000)
    result = parse_json_response(result_text)

    return HookBankResponse(hooks=result.get("hooks", []), niche=niche)


@router.get("/ideas", response_model=ContentIdeasResponse)
async def get_content_ideas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reels_result = await db.execute(
        select(Reel).where(Reel.user_id == current_user.id).order_by(Reel.views.desc()).limit(5)
    )
    top_reels = reels_result.scalars().all()

    context = "general content creator"
    if top_reels:
        captions = [r.caption[:80] for r in top_reels if r.caption]
        context = f"This creator's top content themes: {', '.join(captions)}"

    prompt = f"""Generate 10 trending Instagram Reel content ideas based on current social media trends.

{context}

Return ONLY this JSON:
{{
    "ideas": [
        {{
            "title": "Content idea title",
            "hook": "Suggested opening hook",
            "format": "Tutorial|Story|POV|List|Transformation",
            "why_trending": "Why this is trending now",
            "estimated_engagement": "low|medium|high"
        }}
    ],
    "trending_topics": ["Topic 1", "Topic 2", "Topic 3"]
}}"""

    result_text = await call_groq_async(prompt, max_tokens=4000)
    result = parse_json_response(result_text)

    return ContentIdeasResponse(
        ideas=result.get("ideas", []),
        trending_topics=result.get("trending_topics", []),
    )
