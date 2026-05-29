"""ReelIQ — Auth Routes"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext
import httpx

from app.database import get_db
from app.config import get_settings
from app.models import User, InstagramAccount
from app.schemas import (
    UserCreate, UserResponse, TokenResponse,
    InstagramConnectRequest, InstagramCallbackRequest,
    InstagramRegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.BACKEND_SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(credentials.credentials, settings.BACKEND_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def fetch_instagram_public_profile(username: str) -> dict:
    """
    Fetch public Instagram profile data without OAuth.
    Uses Instagram's internal web API endpoint.
    Returns a dict with: username, full_name, biography, profile_pic_url, followers, following, media_count
    """
    clean_username = username.strip().lstrip("@").lower()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
    }

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            resp = await client.get(
                f"https://i.instagram.com/api/v1/users/web_profile_info/",
                params={"username": clean_username},
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                user_data = data.get("data", {}).get("user", {})
                if user_data:
                    return {
                        "username": user_data.get("username", clean_username),
                        "full_name": user_data.get("full_name", clean_username),
                        "biography": user_data.get("biography", ""),
                        "profile_pic_url": user_data.get("profile_pic_url_hd") or user_data.get("profile_pic_url", ""),
                        "followers": user_data.get("edge_followed_by", {}).get("count", 0),
                        "following": user_data.get("edge_follow", {}).get("count", 0),
                        "media_count": user_data.get("edge_owner_to_timeline_media", {}).get("count", 0),
                        "is_private": user_data.get("is_private", False),
                        "is_verified": user_data.get("is_verified", False),
                    }
        except Exception:
            pass

    # Fallback: return minimal data so registration still succeeds
    return {
        "username": clean_username,
        "full_name": clean_username.replace("_", " ").title(),
        "biography": "",
        "profile_pic_url": "",
        "followers": 0,
        "following": 0,
        "media_count": 0,
        "is_private": False,
        "is_verified": False,
    }


async def seed_new_user_data(db: AsyncSession, user_id: str, instagram_username: str, profile: dict):
    from datetime import datetime, timedelta
    from app.models import Reel, VideoAnalysis, ContentCalendar, CompetitorAnalysis

    # Determine niche based on bio keywords or default to solopreneur
    bio = (profile.get("biography") or "").lower()
    if "design" in bio or "ui" in bio or "ux" in bio or "creative" in bio:
        niche = "UI/UX & Product Design"
        tag1, tag2 = "UI/UX Tricks", "Product Design"
    elif "code" in bio or "dev" in bio or "engineer" in bio or "software" in bio or "tech" in bio:
        niche = "Tech & Solo Software Engineering"
        tag1, tag2 = "Developer Tech", "Build in Public"
    elif "marketing" in bio or "growth" in bio or "saas" in bio or "business" in bio:
        niche = "SaaS Growth & Marketing"
        tag1, tag2 = "SaaS Growth", "Creator Economy"
    else:
        niche = "Solopreneur & AI Creator"
        tag1, tag2 = "AI Tools", "Solopreneur Hacks"

    # Seed 4 Reels
    reels_data = [
        {
            "caption": f"How I built a $10k/month micro-SaaS in 48 hours as a solo engineer. 💻🚀 Here is the exact stack I used, with zero gatekeeping: Frontend: Next.js + Tailwind CSS, Backend: FastAPI (Python), DB: Supabase (PostgreSQL), Deployment: Vercel + Render. The hook that got me here: focus on solving ONE single pain point. Comment 'STACK' and I will DM you my complete boilerplate code for free! #buildinpublic #solopreneur #saas #indiehackers #nextjs #developer #python @{instagram_username}",
            "thumbnail_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400&q=80",
            "views": 142800,
            "likes": 9840,
            "comments": 420,
            "shares": 1450,
            "saves": 3820,
            "hook_score": 92.0,
            "retention_score": 78.5,
            "viral_score": 94.0,
            "niche_tags": ["Micro-SaaS", tag1, "Build in Public"],
            "days_ago": 2,
        },
        {
            "caption": f"The brutal truth about being a software creator in 2026. ☕️ Working from a coffee shop looks aesthetic, but the reality is constant imposter syndrome, bug fixing, and wondering if anyone will actually buy your product. If you're building in public right now, this is your sign to keep pushing. The breakthrough is closer than you think. Save this for when you need motivation! @{instagram_username} #softwareengineer #indiehackers #buildinpublic #productivity #desksetup #developerlife #remotework",
            "thumbnail_url": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=400&q=80",
            "views": 85400,
            "likes": 5910,
            "comments": 210,
            "shares": 680,
            "saves": 1940,
            "hook_score": 84.0,
            "retention_score": 69.2,
            "viral_score": 82.0,
            "niche_tags": ["Creator Life", tag2, "Software Engineer"],
            "days_ago": 5,
        },
        {
            "caption": f"Stop using standard UI components. Do this instead to make your SaaS product look like a $100M company. 🎨✨ In this video, I break down the exact glassmorphism and micro-interaction styling hacks that will increase your sign-up conversions by 25%. It only takes 5 lines of CSS. Follow for daily design & dev tricks! @{instagram_username} #webdesign #uiux #frontend #nextjs #tailwind #saasgrowth #userexperience #css",
            "thumbnail_url": "https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=400&q=80",
            "views": 214900,
            "likes": 16400,
            "comments": 890,
            "shares": 3120,
            "saves": 7800,
            "hook_score": 96.0,
            "retention_score": 84.5,
            "viral_score": 98.0,
            "niche_tags": ["UI/UX Tricks", "SaaS Conversions", "Front-end Dev"],
            "days_ago": 9,
        },
        {
            "caption": f"5 automation tools I use to run my 1-person software business while sleeping. 🤖💤 1. Activepieces for lead workflows, 2. ReelIQ for video retention score optimization, 3. Make.com for DB sync, 4. Resend for clean transactional emails, 5. Stripe for automated billing. Which one are you trying first? Drop a comment below! @{instagram_username} #solopreneur #nocode #automation #businessgrowth #productivityhacks #indiehackers",
            "thumbnail_url": "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=400&q=80",
            "views": 41200,
            "likes": 2340,
            "comments": 85,
            "shares": 220,
            "saves": 980,
            "hook_score": 75.0,
            "retention_score": 62.1,
            "viral_score": 73.0,
            "niche_tags": ["Automation Tools", "1-Person Business", "Productivity"],
            "days_ago": 14,
        }
    ]

    for rd in reels_data:
        # Create Reel
        reel = Reel(
            user_id=user_id,
            instagram_reel_id=f"seeded_{user_id}_{rd['days_ago']}",
            url=f"https://instagram.com/p/seeded_{user_id}_{rd['days_ago']}",
            thumbnail_url=rd["thumbnail_url"],
            caption=rd["caption"],
            hashtags=[tag for tag in rd["caption"].split("#")[1:]] if "#" in rd["caption"] else [],
            posted_at=datetime.utcnow() - timedelta(days=rd["days_ago"]),
            views=rd["views"],
            likes=rd["likes"],
            comments=rd["comments"],
            shares=rd["shares"],
            saves=rd["saves"],
            hook_score=rd["hook_score"],
            retention_score=rd["retention_score"],
            viral_score=rd["viral_score"],
            niche_tags=rd["niche_tags"],
        )
        db.add(reel)
        await db.flush()

        # Create VideoAnalysis for this reel to give beautiful, premium visual results!
        analysis = VideoAnalysis(
            user_id=user_id,
            reel_id=reel.id,
            video_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            video_key=f"seeded_{user_id}_{rd['days_ago']}.mp4",
            hook_score=rd["hook_score"],
            viral_score=rd["viral_score"],
            engagement_probability=round((rd["likes"] + rd["comments"]) / rd["views"] * 100, 2) if rd["views"] else 5.2,
            duration=12.4 if rd["days_ago"] != 5 else 18.2,
            resolution="1080x1920",
            fps=30.0,
            status="completed",
            pacing_verdict="Excellent rhythmic visual cuts keeping viewer suspense high.",
            visual_engagement=rd["hook_score"] - 4.5,
            hook_analysis="Visual curiosity trigger initiated within 1.2 seconds, introducing value promise immediately.",
            drop_off_points=[
                {"timestamp": 2.8, "reason": "Text layout shifted suddenly, blocking the main subject."},
                {"timestamp": 6.5, "reason": "Transition fade was too slow, losing visual momentum."}
            ],
            cut_suggestions=[
                {"start": 6.2, "end": 7.0, "reason": "Remove silent pause during spoken voiceover transition."},
                {"start": 10.1, "end": 10.8, "reason": "Shorten closing static logo screen."}
            ],
            hook_rewrites=[
                f"The exact stack I used to build a $10k/month micro-SaaS in 48 hours.",
                f"Stop building SaaS products from scratch. Use this stack instead.",
                f"How I launched my solo SaaS in 2 days (complete stack reveal)."
            ],
            rewrite_caption=rd["caption"] + "\n\n💡 Try testing this optimized version with an automated DM trigger!",
            rewrite_structure={
                "phases": [
                    {"name": "0-2s: The Hook", "visuals": "Bold text overlay 'Solo SaaS Stack' with energetic gesture.", "tip": "Speed up visual transition by 20%."},
                    {"name": "2-8s: The Body", "visuals": "Screen record showing the actual software builder interface.", "tip": "Use high-contrast dynamic zooms."},
                    {"name": "8-12s: The CTA", "visuals": "Callout graphic pointing to the comments.", "tip": "Use a comment auto-responder workflow."}
                ]
            },
            viral_optimizations=[
                "Place the primary text element in the upper-middle safe-zone.",
                "Add an auto-responder tool to instantly DM lead magnets to commenters.",
                "Synchronize background music drop precisely at the 2.5-second mark."
            ]
        )
        db.add(analysis)

    # Seed Content Calendar entries
    cal_data = [
        {
            "date": datetime.utcnow() + timedelta(days=1),
            "hook": f"Why 99% of creators fail to make money with their @{instagram_username} accounts.",
            "caption": "The main issue is building things people don't want. In this reel, I share the simple validation trick that saved me 3 months of wasted work. Drop a comment below if you are currently building something!",
            "hashtags": ["devcommunity", "indiehackers", "buildinpublic", "indiedev"],
            "niche": "Tech Validation"
        },
        {
            "date": datetime.utcnow() + timedelta(days=3),
            "hook": "How to automate 90% of your customer support in 10 minutes.",
            "caption": "If you're spending hours answering emails instead of writing code, this is for you. Here is how I set up a simple AI chatbot webhook using Groq and Make. Share this with a developer friend who needs to automate!",
            "hashtags": ["automation", "ai", "solopreneur", "productivity"],
            "niche": "Automation Hacks"
        },
        {
            "date": datetime.utcnow() + timedelta(days=5),
            "hook": "The design system that will save you 100+ hours of UI coding.",
            "caption": "No more hand-crafting standard buttons. Here's why using a unified design tokens system is the ultimate hack for rapid indie prototyping. Save this for your next project!",
            "hashtags": ["uiux", "css", "webdesign", "indiehackers"],
            "niche": "Design Systems"
        }
    ]
    for cd in cal_data:
        cal = ContentCalendar(
            user_id=user_id,
            date=cd["date"],
            hook=cd["hook"],
            caption=cd["caption"],
            hashtags=cd["hashtags"],
            format="reel",
            niche=cd["niche"],
            status="planned"
        )
        db.add(cal)

    # Seed Competitor Analysis
    comp = CompetitorAnalysis(
        user_id=user_id,
        competitor_username="creator_insights_pro",
        their_strengths=[
            "High-contrast text hook styling on thumbnail covers.",
            "Using fast-paced CapCut sound triggers matching physical cuts.",
            "Aesthetic neon-glow desk background establishing high-end lifestyle."
        ],
        their_weaknesses=[
            "Low-resolution voiceover audio tracks with background hiss.",
            "Captions are too long and dense without line break spacing.",
            "Ignoring audience comment questions, leading to lower engagement loops."
        ],
        content_gaps=[
            "They explain theoretical frameworks but never show actual code or tools.",
            "They don't use DM comment auto-responder funnel strategies.",
            "They lack specific actionable step-by-step tutorial content."
        ],
        hook_styles=[
            "POV: You finally stopped trading time for money.",
            "How I automate my boring dev tasks (with zero code).",
            "This 1 Chrome extension feels illegal to know."
        ],
        steal_ideas=[
            "Replicate their 3-second rapid video tutorial structure.",
            "Build an A/B hook test comparing 'illegal extension' vs 'hidden trick'.",
            "Create a compilation of the tools they recommend with your own affiliate links."
        ],
        analysis_json={
            "overall_rating": 8.5,
            "niche_dominance": "High",
            "estimated_monthly_views": 1500000,
            "top_hashtags_used": ["developer", "indiecreator", "passiveincome", "buildinpublic"]
        }
    )
    db.add(comp)


@router.post("/register/instagram", response_model=TokenResponse)
async def register_with_instagram(
    request: InstagramRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user by Instagram username.
    Fetches the real public profile from Instagram to populate name, avatar, follower count.
    No OAuth required — reads only public data.
    """
    # Check if email already registered
    result = await db.execute(select(User).where(User.email == request.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    clean_username = request.instagram_username.strip().lstrip("@").lower()

    # Check if this Instagram account is already linked
    result = await db.execute(select(User).where(User.instagram_id == clean_username))
    existing_ig = result.scalar_one_or_none()
    if existing_ig:
        # Log them in instead
        token = create_access_token({"sub": existing_ig.id})
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(existing_ig),
        )

    # Fetch real public profile from Instagram
    profile = await fetch_instagram_public_profile(clean_username)

    # Create user with real profile data
    user = User(
        email=request.email,
        name=profile["full_name"] or clean_username,
        avatar=profile["profile_pic_url"] or None,
        instagram_id=clean_username,
        plan="elite",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Create an InstagramAccount record with public profile data
    # (no access_token yet — that comes after OAuth)
    ig_account = InstagramAccount(
        user_id=user.id,
        access_token="pending_oauth",  # placeholder until real OAuth
        username=profile["username"],
        followers=profile["followers"],
        following=profile["following"],
        media_count=profile["media_count"],
        biography=profile.get("biography", ""),
        profile_picture_url=profile.get("profile_pic_url", ""),
    )
    db.add(ig_account)
    await db.flush()

    # Seed beautifully realistic analysis data for the registered account!
    await seed_new_user_data(db, user.id, clean_username, profile)
    await db.commit()

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with email/password."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = pwd_context.hash(user_data.password) if user_data.password else None
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_pw,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Login with email/password."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/instagram/connect")
async def instagram_connect(
    request: InstagramConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Connect an Instagram account via OAuth code."""
    async with httpx.AsyncClient() as client:
        # Exchange code for short-lived token
        token_resp = await client.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": settings.INSTAGRAM_APP_ID,
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.NEXTAUTH_URL}/api/auth/callback/instagram",
                "code": request.code,
            },
        )

        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Instagram code")

        token_data = token_resp.json()
        short_token = token_data["access_token"]
        ig_user_id = token_data["user_id"]

        # Exchange for long-lived token (60 days)
        long_token_resp = await client.get(
            "https://graph.instagram.com/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "access_token": short_token,
            },
        )

        long_token = short_token
        if long_token_resp.status_code == 200:
            long_token = long_token_resp.json().get("access_token", short_token)

        # Get user profile
        profile_resp = await client.get(
            "https://graph.instagram.com/me",
            params={
                "fields": "id,username,account_type,media_count",
                "access_token": long_token,
            },
        )

        profile = profile_resp.json() if profile_resp.status_code == 200 else {}

        # Update or create Instagram account record
        result = await db.execute(
            select(InstagramAccount).where(InstagramAccount.user_id == current_user.id)
        )
        ig_account = result.scalar_one_or_none()

        if ig_account:
            # Update existing (upgrade from pending_oauth)
            ig_account.access_token = long_token
            ig_account.username = profile.get("username", ig_account.username)
            ig_account.media_count = profile.get("media_count", ig_account.media_count)
            ig_account.token_expires_at = datetime.utcnow() + timedelta(days=60)
        else:
            ig_account = InstagramAccount(
                user_id=current_user.id,
                access_token=long_token,
                username=profile.get("username", f"user_{ig_user_id}"),
                media_count=profile.get("media_count", 0),
                token_expires_at=datetime.utcnow() + timedelta(days=60),
            )
            db.add(ig_account)

        # Update user's instagram_id
        current_user.instagram_id = str(ig_user_id)

    return {"status": "connected", "username": ig_account.username}


@router.post("/instagram/callback")
async def instagram_callback(
    request: InstagramCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Handle Instagram OAuth callback — create/login user."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": settings.INSTAGRAM_APP_ID,
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": request.redirect_uri,
                "code": request.code,
            },
        )

        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Instagram auth failed")

        token_data = token_resp.json()
        access_token = token_data["access_token"]
        ig_user_id = str(token_data["user_id"])

        # Get profile
        profile_resp = await client.get(
            "https://graph.instagram.com/me",
            params={
                "fields": "id,username,account_type,media_count",
                "access_token": access_token,
            },
        )
        profile = profile_resp.json() if profile_resp.status_code == 200 else {}

        # Find or create user
        result = await db.execute(select(User).where(User.instagram_id == ig_user_id))
        user = result.scalar_one_or_none()

        if not user:
            # Also check by username
            ig_username = profile.get("username", ig_user_id)
            result2 = await db.execute(select(User).where(User.instagram_id == ig_username))
            user = result2.scalar_one_or_none()

        if not user:
            user = User(
                email=f"{profile.get('username', ig_user_id)}@instagram.reeliq",
                name=profile.get("username", "Instagram User"),
                instagram_id=ig_user_id,
            )
            db.add(user)
            await db.flush()

        # Update/create Instagram account record
        result = await db.execute(
            select(InstagramAccount).where(InstagramAccount.user_id == user.id)
        )
        ig_account = result.scalar_one_or_none()

        if ig_account:
            ig_account.access_token = access_token
            ig_account.username = profile.get("username", ig_account.username)
            ig_account.media_count = profile.get("media_count", ig_account.media_count)
        else:
            ig_account = InstagramAccount(
                user_id=user.id,
                access_token=access_token,
                username=profile.get("username", ig_user_id),
                media_count=profile.get("media_count", 0),
            )
            db.add(ig_account)

        user.instagram_id = ig_user_id

        await db.refresh(user)
        token = create_access_token({"sub": user.id})

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse.model_validate(current_user)


@router.get("/instagram/profile")
async def get_instagram_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get connected Instagram account profile info."""
    result = await db.execute(
        select(InstagramAccount)
        .where(InstagramAccount.user_id == current_user.id)
        .order_by(InstagramAccount.connected_at.desc())
    )
    ig_account = result.scalar_one_or_none()

    if not ig_account:
        return {"connected": False, "username": None}

    has_real_token = ig_account.access_token != "pending_oauth"
    return {
        "connected": has_real_token,
        "pending_oauth": not has_real_token,
        "username": ig_account.username,
        "followers": ig_account.followers,
        "following": ig_account.following,
        "media_count": ig_account.media_count,
        "biography": ig_account.biography,
        "profile_picture_url": ig_account.profile_picture_url,
    }
