"""ReelIQ — Celery Analysis Tasks (Account, Competitor, etc.)"""
import json
from datetime import datetime

from app.workers import celery_app
from app.ai_client import call_groq, parse_json_response
from app.database import SyncSessionLocal
from app.models import Reel, CompetitorAnalysis, User
from app.prompts.account_analysis_prompt import build_account_analysis_prompt
from app.prompts.competitor_analysis_prompt import build_competitor_analysis_prompt


@celery_app.task(bind=True, name="analyze_account", max_retries=2)
def analyze_account_task(self, user_id: str):
    """Full account analysis: fetch all reels, send to Groq for analysis."""
    db = SyncSessionLocal()

    try:
        self.update_state(state="PROGRESS", meta={"step": "fetching_reels", "progress": 20})

        reels = db.query(Reel).filter(Reel.user_id == user_id).order_by(Reel.posted_at.desc()).all()

        if not reels:
            return {"error": "No reels found for analysis"}

        # Build reels data for prompt
        reels_data = []
        for reel in reels:
            reels_data.append({
                "caption": reel.caption,
                "hashtags": reel.hashtags or [],
                "posted_at": str(reel.posted_at),
                "views": reel.views,
                "likes": reel.likes,
                "comments": reel.comments,
                "shares": reel.shares,
                "saves": reel.saves,
                "duration": reel.duration,
                "audio_name": reel.audio_name,
            })

        self.update_state(state="PROGRESS", meta={"step": "analyzing", "progress": 50})

        prompt = build_account_analysis_prompt(reels_data)
        result_text = call_groq(prompt, max_tokens=8000)
        result = parse_json_response(result_text)

        self.update_state(state="PROGRESS", meta={"step": "storing", "progress": 90})

        # Update user's reels with niche tags and scores from analysis
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Store the full analysis on the user (we can use the first reel's analysis_json as account-level)
            if reels:
                reels[0].analysis_json = result

        db.commit()

        return {
            "status": "completed",
            "analysis": result,
        }

    except Exception as e:
        raise self.retry(exc=e, countdown=30)

    finally:
        db.close()


@celery_app.task(bind=True, name="analyze_competitor", max_retries=2)
def analyze_competitor_task(self, user_id: str, competitor_username: str, their_posts: list = None):
    """Analyze a competitor's content strategy."""
    db = SyncSessionLocal()

    try:
        self.update_state(state="PROGRESS", meta={"step": "analyzing", "progress": 40})

        # Get user's own stats for comparison
        user_reels = db.query(Reel).filter(Reel.user_id == user_id).all()
        your_stats = None
        if user_reels:
            total_views = sum(r.views for r in user_reels)
            total_likes = sum(r.likes for r in user_reels)
            your_stats = {
                "total_reels": len(user_reels),
                "avg_views": total_views // len(user_reels) if user_reels else 0,
                "avg_likes": total_likes // len(user_reels) if user_reels else 0,
            }

        prompt = build_competitor_analysis_prompt(
            competitor_username=competitor_username,
            their_posts=their_posts,
            your_stats=your_stats,
        )
        result_text = call_groq(prompt, max_tokens=6000)
        result = parse_json_response(result_text)

        self.update_state(state="PROGRESS", meta={"step": "storing", "progress": 80})

        # Store competitor analysis
        comp_analysis = CompetitorAnalysis(
            user_id=user_id,
            competitor_username=competitor_username,
            analysis_json=result,
            their_strengths=result.get("their_strengths", []),
            their_weaknesses=result.get("their_weaknesses", []),
            content_gaps=result.get("content_gaps_you_can_fill", []),
            hook_styles=result.get("hook_styles_they_use", []),
            steal_ideas=result.get("steal_these_ideas", []),
        )
        db.add(comp_analysis)
        db.commit()

        return {
            "status": "completed",
            "analysis_id": comp_analysis.id,
            "analysis": result,
        }

    except Exception as e:
        raise self.retry(exc=e, countdown=30)

    finally:
        db.close()
