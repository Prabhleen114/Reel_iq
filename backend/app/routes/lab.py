"""ReelIQ — Content Lab Routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, ABTest, VideoAnalysis
from app.schemas import (
    ViralScoreRequest, ViralScoreResponse,
    ABTestRequest, ABTestResponse,
    ReelRewriteRequest, ReelRewriteResponse,
)
from app.routes.auth import get_current_user
from app.ai_client import call_groq_async, parse_json_response
from app.prompts.viral_score_prompt import build_viral_score_prompt
from app.prompts.hook_score_prompt import build_hook_score_prompt
from app.prompts.reel_rewrite_prompt import build_reel_rewrite_prompt

router = APIRouter(prefix="/lab", tags=["Content Lab"])


@router.post("/viral-score", response_model=ViralScoreResponse)
async def predict_viral_score(
    request: ViralScoreRequest,
    current_user: User = Depends(get_current_user),
):
    prompt = build_viral_score_prompt(
        hook=request.hook,
        caption=request.caption,
        niche=request.niche,
        hashtags=request.hashtags,
    )
    result_text = await call_groq_async(prompt)
    result = parse_json_response(result_text)

    return ViralScoreResponse(
        viral_score=result.get("viral_score", 0),
        confidence=result.get("confidence", "medium"),
        key_signals=result.get("key_signals", []),
        missing_elements=result.get("missing_elements", []),
        predicted_reach_multiplier=result.get("predicted_reach_multiplier", 1.0),
    )


@router.post("/ab-test", response_model=ABTestResponse)
async def ab_test_hooks(
    request: ABTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Score hook A
    prompt_a = build_hook_score_prompt(request.hook_a, request.niche)
    result_a_text = await call_groq_async(prompt_a)
    result_a = parse_json_response(result_a_text)

    # Score hook B
    prompt_b = build_hook_score_prompt(request.hook_b, request.niche)
    result_b_text = await call_groq_async(prompt_b)
    result_b = parse_json_response(result_b_text)

    score_a = result_a.get("score", 50)
    score_b = result_b.get("score", 50)
    winner = "a" if score_a >= score_b else "b"

    # Generate verdict
    verdict_prompt = f"""Compare these two Instagram hooks and explain which is better and why in 2-3 sentences.

Hook A (score: {score_a}): "{request.hook_a}"
Hook B (score: {score_b}): "{request.hook_b}"

Winner: Hook {'A' if winner == 'a' else 'B'}. Explain why in 2-3 concise sentences. Return only the explanation text, no JSON."""

    verdict = await call_groq_async(verdict_prompt, max_tokens=500)

    # Store test
    ab_test = ABTest(
        user_id=current_user.id,
        hook_a=request.hook_a,
        hook_b=request.hook_b,
        niche=request.niche,
        predicted_score_a=score_a,
        predicted_score_b=score_b,
        analysis_a=result_a,
        analysis_b=result_b,
        winner=winner,
        verdict=verdict.strip(),
    )
    db.add(ab_test)
    await db.flush()
    await db.refresh(ab_test)

    return ABTestResponse(
        id=ab_test.id,
        hook_a=request.hook_a,
        hook_b=request.hook_b,
        predicted_score_a=score_a,
        predicted_score_b=score_b,
        winner=winner,
        verdict=verdict.strip(),
        analysis_a=result_a,
        analysis_b=result_b,
    )


@router.post("/rewrite-reel", response_model=ReelRewriteResponse)
async def rewrite_reel(
    request: ReelRewriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video_analysis = None
    if request.video_analysis_id:
        result = await db.execute(
            select(VideoAnalysis).where(
                VideoAnalysis.id == request.video_analysis_id,
                VideoAnalysis.user_id == current_user.id,
            )
        )
        va = result.scalar_one_or_none()
        if va:
            video_analysis = {
                "hook_score": va.hook_score,
                "hook_analysis": va.hook_analysis,
                "drop_off_points": va.drop_off_points,
                "pacing_verdict": va.pacing_verdict,
            }

    prompt = build_reel_rewrite_prompt(
        hook=request.hook,
        caption=request.caption,
        video_analysis=video_analysis,
        niche=request.niche,
    )
    result_text = await call_groq_async(prompt)
    result = parse_json_response(result_text)

    return ReelRewriteResponse(
        new_hook=result.get("new_hook", ""),
        hook_psychology=result.get("hook_psychology", ""),
        new_caption=result.get("new_caption", ""),
        new_structure=result.get("new_structure", []),
        viral_potential_after=result.get("viral_potential_after", 0),
        what_changed=result.get("what_changed", ""),
    )
