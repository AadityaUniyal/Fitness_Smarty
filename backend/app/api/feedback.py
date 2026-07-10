"""
Feedback API Router — Collect, store, and respond to user feedback.
Table: user_feedback (PostgreSQL via Neon)
"""

import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])
logger = logging.getLogger(__name__)

# ──────────────────────────
# Pydantic Schemas
# ──────────────────────────


class FeedbackCreate(BaseModel):
    user_id: str
    rating: int = Field(..., ge=1, le=5, description="Star rating 1–5")
    category: str = Field(default="general")
    message: str = Field(..., min_length=5, max_length=2000)
    module: Optional[str] = None
    is_anonymous: bool = False

    @validator("category")
    def valid_category(cls, v):
        allowed = {
            "bug_report",
            "feature_request",
            "general",
            "ai_quality",
            "ux",
            "performance",
        }
        if v not in allowed:
            raise ValueError(f"Category must be one of {allowed}")
        return v


class FeedbackResponse(BaseModel):
    id: int
    user_id: str
    rating: int
    category: str
    message: str
    module: Optional[str]
    sentiment: Optional[str]
    status: str
    ai_response: Optional[str]
    is_anonymous: bool
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    total: int
    avg_rating: float
    by_category: dict
    by_sentiment: dict
    by_status: dict
    recent_count: int  # last 7 days


# ──────────────────────────
# Sentiment Detection (simple rule-based + Gemini optional)
# ──────────────────────────


def detect_sentiment(message: str, rating: int) -> str:
    if rating >= 4:
        return "positive"
    elif rating <= 2:
        return "negative"
    # For 3-star, check message keywords
    negative_words = {
        "crash",
        "broken",
        "bug",
        "error",
        "fail",
        "terrible",
        "wrong",
        "slow",
        "awful",
        "bad",
    }
    positive_words = {
        "great",
        "love",
        "amazing",
        "excellent",
        "perfect",
        "fast",
        "good",
        "awesome",
        "helpful",
    }
    lower = message.lower()
    if any(w in lower for w in negative_words):
        return "negative"
    if any(w in lower for w in positive_words):
        return "positive"
    return "neutral"


async def generate_ai_acknowledgement(
    rating: int, category: str, message: str
) -> str:
    """Optional Gemini-powered acknowledgement. Falls back gracefully."""
    try:
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return None
        client = genai.Client(api_key=api_key)
        prompt = (
            f"A user gave {rating}/5 stars for category '{category}' with "
            f"this feedback: '{message[:200]}'. Write a warm, professional "
            "1-sentence acknowledgement (max 30 words). Be genuine."
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return response.text.strip()
    except Exception:
        return None


def send_feedback_email(
    rating: int,
    category: str,
    message: str,
    user_id: str,
    sentiment: str,
    module: Optional[str] = None,
):
    """Asynchronously dispatches an SMTP email notification of user feedback"""
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM_EMAIL", smtp_username)
    smtp_to = os.environ.get("SMTP_TO_EMAIL")
    if os.environ.get("ENABLE_FEEDBACK_EMAILS", "false").lower() not in {
        "1",
        "true",
        "yes",
    }:
        logger.info("Feedback email notifications disabled by configuration.")
        return

    if not all([smtp_host, smtp_port, smtp_username, smtp_password, smtp_to]):
        logger.warning(
            "SMTP mailer not fully configured in environment. "
            "Skipping feedback email notification."
        )
        return

    try:
        port = int(smtp_port)
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = smtp_to
        msg["Subject"] = (
            f"🔔 [Smarty Feedback] New {category.replace('_', ' ').title()} "
            f"- {rating}/5 Stars"
        )

        body = (
            "<html>\n"
            "<body style=\"font-family: Arial, sans-serif; color: #333; line-height: 1.6;\">\n"
            "    <div style=\"max-width: 600px; margin: 0 auto; padding: 20px; "
            "border: 1px solid #e0e0e0; border-radius: 12px; background-color: #fafafa;\">\n"
            "        <h2 style=\"color: #8b5cf6; border-bottom: 2px solid #8b5cf6; "
            "padding-bottom: 8px;\">New User Feedback Logged</h2>\n"
            f"        <p><strong>User Node:</strong> {user_id}</p>\n"
            f"        <p><strong>Rating:</strong> {rating}/5 Stars</p>\n"
            f"        <p><strong>Category:</strong> {category.replace('_', ' ').upper()}</p>\n"
            f"        <p><strong>Module context:</strong> {module or 'N/A'}</p>\n"
            f"        <p><strong>Sentiment:</strong> <span style=\"font-weight: bold; color: "
            f"{'#10b981' if sentiment == 'positive' else '#f43f5e' if sentiment == 'negative' else '#64748b'}"
            f';">{sentiment.upper()}</span></p>\n'
            "        <hr style=\"border: 0; border-top: 1px solid #e0e0e0; margin: 20px 0;\" />\n"
            "        <p><strong>Message:</strong></p>\n"
            "        <blockquote style=\"background-color: #ffffff; padding: 15px; "
            "border-left: 4px solid #8b5cf6; margin: 10px 0; font-style: italic; border-radius: 4px;\">\n"
            f"            {message}\n"
            "        </blockquote>\n"
            "        <hr style=\"border: 0; border-top: 1px solid #e0e0e0; margin: 20px 0;\" />\n"
            "        <p style=\"font-size: 10px; color: #888; text-align: center;\">"
            "Smarty AI Neural Platform • Automated Notification System</p>\n"
            "    </div>\n"
            "</body>\n"
            "</html>"
        )
        msg.attach(MIMEText(body, "html"))

        # Secure connection
        server = smtplib.SMTP(smtp_host, port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from, smtp_to, msg.as_string())
        server.quit()
        logger.info(
            "Successfully dispatched feedback email alert notification to %s",
            smtp_to,
        )
    except Exception:
        logger.exception(
            "Critical error occurred while dispatching "
            "feedback email notification"
        )


# ──────────────────────────
# Routes
# ──────────────────────────


@router.post("/", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    data: FeedbackCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Submit new user feedback.

    Auto-detects sentiment and optionally generates AI acknowledgement.
    """
    sentiment = detect_sentiment(data.message, data.rating)
    ai_response = await generate_ai_acknowledgement(
        data.rating, data.category, data.message
    )

    feedback = models.UserFeedback(
        user_id="anonymous" if data.is_anonymous else data.user_id,
        rating=data.rating,
        category=data.category,
        message=data.message,
        module=data.module,
        sentiment=sentiment,
        ai_response=ai_response,
        is_anonymous=data.is_anonymous,
        status="open",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    # Queue background email alert
    background_tasks.add_task(
        send_feedback_email,
        rating=data.rating,
        category=data.category,
        message=data.message,
        user_id="anonymous" if data.is_anonymous else data.user_id,
        sentiment=sentiment,
        module=data.module,
    )

    return feedback


@router.get("/user/{user_id}", response_model=List[FeedbackResponse])
def get_user_feedback(
    user_id: str,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """Get all feedback submitted by a specific user."""
    results = (
        db.query(models.UserFeedback)
        .filter(models.UserFeedback.user_id == user_id)
        .order_by(models.UserFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    return results


@router.get("/stats", response_model=FeedbackStats)
def get_feedback_stats(db: Session = Depends(get_db)):
    """Aggregate stats across all feedback entries."""
    from datetime import timedelta

    all_fb = db.query(models.UserFeedback).all()
    total = len(all_fb)
    avg_rating = (
        round(sum(f.rating for f in all_fb) / total, 2) if total else 0.0
    )

    by_category: dict = {}
    by_sentiment: dict = {}
    by_status: dict = {}

    for f in all_fb:
        by_category[f.category] = by_category.get(f.category, 0) + 1
        by_sentiment[f.sentiment or "unknown"] = (
            by_sentiment.get(f.sentiment or "unknown", 0) + 1
        )
        by_status[f.status] = by_status.get(f.status, 0) + 1

    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = (
        db.query(models.UserFeedback)
        .filter(models.UserFeedback.created_at >= week_ago)
        .count()
    )

    return FeedbackStats(
        total=total,
        avg_rating=avg_rating,
        by_category=by_category,
        by_sentiment=by_sentiment,
        by_status=by_status,
        recent_count=recent_count,
    )


@router.get("/all", response_model=List[FeedbackResponse])
def get_all_feedback(
    limit: int = Query(default=50, le=200),
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Admin: get all feedback with optional filters."""
    q = db.query(models.UserFeedback).order_by(
        models.UserFeedback.created_at.desc()
    )
    if category:
        q = q.filter(models.UserFeedback.category == category)
    if sentiment:
        q = q.filter(models.UserFeedback.sentiment == sentiment)
    return q.limit(limit).all()


@router.patch("/{feedback_id}/status")
def update_feedback_status(
    feedback_id: int,
    status: str = Query(..., regex="^(open|reviewed|resolved)$"),
    db: Session = Depends(get_db),
):
    """Mark a feedback entry as reviewed or resolved."""
    fb = (
        db.query(models.UserFeedback)
        .filter(models.UserFeedback.id == feedback_id)
        .first()
    )
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    fb.status = status
    fb.updated_at = datetime.utcnow()
    db.commit()
    return {"message": f"Feedback {feedback_id} marked as {status}"}


class CoachFeedbackCreate(BaseModel):
    domain: str = Field(..., pattern="^(exercise|meal|daily_plan)$")
    item_id: str
    rating: int = Field(..., ge=0, le=5)
    context_json: Optional[dict] = None


@router.post("/coach")
def create_coach_feedback(
    data: CoachFeedbackCreate,
    current_user: models.EnhancedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    feedback = models.CoachFeedback(
        user_id=str(current_user.id),
        domain=data.domain,
        item_id=data.item_id,
        rating=data.rating,
        context_json=data.context_json,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    if data.domain == "meal":
        try:
            import json

            filepath = "app/training/datasets/meal_feedback.jsonl"
            import os

            os.makedirs("app/training/datasets", exist_ok=True)
            with open(filepath, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "user_id": str(current_user.id),
                            "meal_log_id": data.item_id,
                            "rating": data.rating,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    + "\n"
                )
        except Exception as e:
            logger.warning(f"Failed to append meal feedback to jsonl: {e}")

    return {"status": "success", "feedback_id": feedback.id}


@router.get("/coach/count")
def get_coach_feedback_count(db: Session = Depends(get_db)):
    count = db.query(models.CoachFeedback).count()
    return {"count": count}
