"""ReelIQ — Competitor Analysis Routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, CompetitorAnalysis
from app.schemas import CompetitorAnalyzeRequest, CompetitorAnalysisResponse
from app.routes.auth import get_current_user
from app.workers.analysis_tasks import analyze_competitor_task

router = APIRouter(prefix="/competitor", tags=["Competitor Analysis"])


@router.post("/analyze")
async def analyze_competitor(
    request: CompetitorAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = analyze_competitor_task.delay(
        current_user.id,
        request.competitor_username,
        request.their_posts,
    )
    return {
        "job_id": task.id,
        "status": "queued",
        "message": f"Analyzing @{request.competitor_username}. Poll /analyze/status/{task.id}",
    }


@router.get("/history")
async def get_competitor_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CompetitorAnalysis)
        .where(CompetitorAnalysis.user_id == current_user.id)
        .order_by(CompetitorAnalysis.created_at.desc())
        .limit(20)
    )
    analyses = result.scalars().all()
    return [CompetitorAnalysisResponse.model_validate(a) for a in analyses]
