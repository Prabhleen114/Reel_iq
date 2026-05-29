"""ReelIQ — Instagram Data Routes"""
import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import httpx

from app.database import get_db
from app.models import User, InstagramAccount, Reel
from app.schemas import ReelResponse, ReelListResponse, ImportRequest
from app.routes.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/instagram", tags=["Instagram Data"])
settings = get_settings()


def extract_hashtags(caption: str) -> list:
    """Extract hashtags from a caption string."""
    if not caption:
        return []
    return re.findall(r"#(\w+)", caption)


@router.post("/sync")
async def sync_reels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all reels from Instagram API and sync to database."""
    # Get user's Instagram account
    result = await db.execute(
        select(InstagramAccount)
        .where(InstagramAccount.user_id == current_user.id)
        .order_by(InstagramAccount.connected_at.desc())
    )
    ig_account = result.scalar_one_or_none()

    if not ig_account:
        raise HTTPException(status_code=400, detail="No Instagram account connected")

    synced_count = 0
    after_cursor = None

    async with httpx.AsyncClient() as client:
        while True:
            params = {
                "fields": "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink,like_count,comments_count",
                "access_token": ig_account.access_token,
                "limit": 50,
            }
            if after_cursor:
                params["after"] = after_cursor

            resp = await client.get(
                f"https://graph.instagram.com/me/media",
                params=params,
            )

            if resp.status_code != 200:
                break

            data = resp.json()
            media_items = data.get("data", [])

            for item in media_items:
                # Only process VIDEO (reels)
                if item.get("media_type") not in ("VIDEO", "REELS"):
                    continue

                ig_reel_id = item["id"]

                # Check if already exists
                existing = await db.execute(
                    select(Reel).where(Reel.instagram_reel_id == ig_reel_id)
                )
                if existing.scalar_one_or_none():
                    continue

                caption = item.get("caption", "")
                reel = Reel(
                    user_id=current_user.id,
                    instagram_reel_id=ig_reel_id,
                    url=item.get("media_url"),
                    thumbnail_url=item.get("thumbnail_url"),
                    caption=caption,
                    hashtags=extract_hashtags(caption),
                    posted_at=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")) if item.get("timestamp") else None,
                    likes=item.get("like_count", 0),
                    comments=item.get("comments_count", 0),
                    views=0,  # Basic Display API doesn't return views directly
                )
                db.add(reel)
                synced_count += 1

            # Pagination
            paging = data.get("paging", {})
            after_cursor = paging.get("cursors", {}).get("after")
            if not after_cursor or "next" not in paging:
                break

    return {"synced": synced_count, "total_reels": synced_count}


@router.post("/reels", response_model=ReelResponse)
async def create_manual_reel(
    reel_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually create a reel (e.g. from upload analysis)."""
    import uuid
    
    reel = Reel(
        user_id=current_user.id,
        instagram_reel_id=reel_data.get("instagram_reel_id") or f"manual_{uuid.uuid4().hex[:8]}",
        url=reel_data.get("url"),
        thumbnail_url=reel_data.get("thumbnail_url"),
        caption=reel_data.get("caption"),
        hashtags=reel_data.get("hashtags") or [],
        duration=reel_data.get("duration"),
        audio_name=reel_data.get("audio_name") or "Original Audio",
        posted_at=datetime.utcnow(),
        views=reel_data.get("views", 0),
        likes=reel_data.get("likes", 0),
        comments=reel_data.get("comments", 0),
        shares=reel_data.get("shares", 0),
        saves=reel_data.get("saves", 0),
        hook_score=reel_data.get("hook_score"),
        viral_score=reel_data.get("viral_score"),
        retention_score=reel_data.get("retention_score"),
        niche_tags=reel_data.get("niche_tags") or ["Custom"],
        analysis_json=reel_data.get("analysis_json"),
    )
    db.add(reel)
    await db.commit()
    await db.refresh(reel)
    return reel


@router.post("/import")
async def import_reels(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import reels from exported JSON data (Instagram data download)."""
    data = request.data
    imported_count = 0

    # Handle Instagram data export format
    posts = data.get("reels_media", data.get("posts", data.get("media", [])))
    if isinstance(posts, dict):
        posts = posts.get("reels_media", [])

    for post in posts:
        caption = ""
        if isinstance(post, dict):
            # Instagram export format
            media_data = post.get("media", [post])
            if isinstance(media_data, list):
                for media in media_data:
                    caption = media.get("title", media.get("caption", ""))
            else:
                caption = post.get("title", post.get("caption", ""))

            posted_at = None
            timestamp = post.get("creation_timestamp", post.get("taken_at"))
            if timestamp:
                try:
                    posted_at = datetime.fromtimestamp(int(timestamp))
                except (ValueError, TypeError):
                    pass

            reel = Reel(
                user_id=current_user.id,
                caption=caption,
                hashtags=extract_hashtags(caption),
                posted_at=posted_at,
                url=post.get("uri", post.get("url")),
                views=post.get("view_count", post.get("views", 0)),
                likes=post.get("like_count", post.get("likes", 0)),
                comments=post.get("comment_count", post.get("comments", 0)),
                shares=post.get("share_count", post.get("shares", 0)),
                saves=post.get("save_count", post.get("saves", 0)),
            )
            db.add(reel)
            imported_count += 1

    return {"imported": imported_count}


@router.get("/reels", response_model=ReelListResponse)
async def get_reels(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("posted_at", regex="^(posted_at|views|likes|viral_score|hook_score)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated list of user's reels with sorting."""
    # Count total
    count_result = await db.execute(
        select(func.count(Reel.id)).where(Reel.user_id == current_user.id)
    )
    total = count_result.scalar()

    # Get sorted page
    sort_column = getattr(Reel, sort_by, Reel.posted_at)
    order_func = sort_column.desc() if order == "desc" else sort_column.asc()

    result = await db.execute(
        select(Reel)
        .where(Reel.user_id == current_user.id)
        .order_by(order_func)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    reels = result.scalars().all()

    return ReelListResponse(
        reels=[ReelResponse.model_validate(r) for r in reels],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/reels/{reel_id}", response_model=ReelResponse)
async def get_reel(
    reel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single reel with its analysis."""
    result = await db.execute(
        select(Reel).where(Reel.id == reel_id, Reel.user_id == current_user.id)
    )
    reel = result.scalar_one_or_none()
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")

    return ReelResponse.model_validate(reel)
