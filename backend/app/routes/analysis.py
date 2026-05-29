from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User, VideoAnalysis
import uuid

router = APIRouter(prefix="/analyze", tags=["analysis"])

@router.post("/account")
async def analyze_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger a full account analysis."""
    # Here we would normally trigger a background task
    return {"status": "success", "message": "Account analysis triggered"}


@router.post("/reel/{reel_id}")
async def analyze_reel(
    reel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deep analysis of a single reel."""
    # Here we would normally trigger a background task for the reel
    return {"status": "success", "message": f"Reel {reel_id} analysis triggered"}


@router.post("/video")
async def analyze_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and analyze a new video file."""
    if not file.filename.endswith(('.mp4', '.mov', '.webm')):
        raise HTTPException(status_code=400, detail="Invalid video format")
    
    # In a real app, we'd save to R2, then enqueue a celery job
    # For now, simulate returning a job ID
    job_id = str(uuid.uuid4())
    
    # Create an initial VideoAnalysis record
    new_analysis = VideoAnalysis(
        id=job_id,
        user_id=current_user.id,
        video_url="s3://pending-upload",
        status="processing"
    )
    db.add(new_analysis)
    await db.commit()
    
    # Normally: celery_app.send_task("process_video", args=[job_id, "s3://url"])
    
    return {
        "status": "success", 
        "message": "Video analysis started",
        "job_id": job_id
    }


@router.get("/status/{job_id}")
async def get_analysis_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Poll Celery job / database for video analysis status."""
    from sqlalchemy import select
    
    stmt = select(VideoAnalysis).where(VideoAnalysis.id == job_id, VideoAnalysis.user_id == current_user.id)
    result = await db.execute(stmt)
    analysis = result.scalars().first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": analysis.id,
        "status": analysis.status,
        "hook_score": analysis.hook_score,
        "rewrite_structure": analysis.rewrite_structure
    }
