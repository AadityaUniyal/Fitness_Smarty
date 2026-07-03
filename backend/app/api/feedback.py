"""
Feedback API Router — Collect, store, and respond to user feedback.
Table: user_feedback (PostgreSQL via Neon)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


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
        allowed = {"bug_report", "feature_request", "general", "ai_quality", "ux", "performance"}
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
    negative_words = {"crash", "broken", "bug", "error", "fail", "terrible", "wrong", "slow", "awful", "bad"}
    positive_words = {"great", "love", "amazing", "excellent", "perfect", "fast", "good", "awesome", "helpful"}
    lower = message.lower()
    if any(w in lower for w in negative_words):
        return "negative"
    if any(w in lower for w in positive_words):
        return "positive"
    return "neutral"


async def generate_ai_acknowledgement(rating: int, category: str, message: str) -> str:
    """Optional Gemini-powered acknowledgement. Falls back gracefully."""
    import os
    try:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return None
        client = genai.Client(api_key=api_key)
        prompt = (
            f"A user gave {rating}/5 stars for category '{category}' with this feedback: '{message[:200]}'. "
            "Write a warm, professional 1-sentence acknowledgement (max 30 words). Be genuine."
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text.strip()
    except Exception:
        return None


def send_feedback_email(rating: int, category: str, message: str, user_id: str, sentiment: str, module: Optional[str] = None):
    """Asynchronously dispatches an SMTP email notification of user feedback"""
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM_EMAIL", smtp_username)
    smtp_to = os.environ.get("SMTP_TO_EMAIL")

    if not all([smtp_host, smtp_port, smtp_username, smtp_password, smtp_to]):
        print("[Mailer] SMTP mailer not fully configured in environment. Skipping email alert notification.")
        return

    try:
        port = int(smtp_port)
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = smtp_to
        msg['Subject'] = f"🔔 [Smarty Feedback] New {category.replace('_', ' ').title()} - {rating}/5 Stars"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 12px; background-color: #fafafa;">
                <h2 style="color: #8b5cf6; border-bottom: 2px solid #8b5cf6; padding-bottom: 8px;">New User Feedback Logged</h2>
                <p><strong>User Node:</strong> {user_id}</p>
                <p><strong>Rating:</strong> {rating}/5 Stars</p>
                <p><strong>Category:</strong> {category.replace('_', ' ').upper()}</p>
                <p><strong>Module context:</strong> {module or 'N/A'}</p>
                <p><strong>Sentiment:</strong> <span style="font-weight: bold; color: { '#10b981' if sentiment == 'positive' else '#f43f5e' if sentiment == 'negative' else '#64748b' };">{sentiment.upper()}</span></p>
                <hr style="border: 0; border-top: 1px solid #e0e0e0; margin: 20px 0;" />
                <p><strong>Message:</strong></p>
                <blockquote style="background-color: #ffffff; padding: 15px; border-left: 4px solid #8b5cf6; margin: 10px 0; font-style: italic; border-radius: 4px;">
                    {message}
                </blockquote>
                <hr style="border: 0; border-top: 1px solid #e0e0e0; margin: 20px 0;" />
                <p style="font-size: 10px; color: #888; text-align: center;">Smarty AI Neural Platform • Automated Notification System</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        # Secure connection
        server = smtplib.SMTP(smtp_host, port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from, smtp_to, msg.as_string())
        server.quit()
        print(f"[Mailer] Successfully dispatched email alert notification to {smtp_to}")
    except Exception as e:
        print(f"[Mailer] Critical error occurred while dispatching email: {e}")


# ──────────────────────────
# Routes
# ──────────────────────────

@router.post("/", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    data: FeedbackCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """Submit new user feedback. Auto-detects sentiment and optionally generates AI acknowledgement."""
    sentiment = detect_sentiment(data.message, data.rating)
    ai_response = await generate_ai_acknowledgement(data.rating, data.category, data.message)

    feedback = models.UserFeedback(
        user_id="anonymous" if data.is_anonymous else data.user_id,
        rating=data.rating,
        category=data.category,
        message=data.message,
        module=data.module,
        sentiment=sentiment,
        ai_response=ai_response,
        is_anonymous=data.is_anonymous,
        status="open"
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
        module=data.module
    )

    return feedback


@router.get("/user/{user_id}", response_model=List[FeedbackResponse])
def get_user_feedback(
    user_id: str,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db)
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
    from sqlalchemy import func
    from datetime import timedelta

    all_fb = db.query(models.UserFeedback).all()
    total = len(all_fb)
    avg_rating = round(sum(f.rating for f in all_fb) / total, 2) if total else 0.0

    by_category: dict = {}
    by_sentiment: dict = {}
    by_status: dict = {}

    for f in all_fb:
        by_category[f.category] = by_category.get(f.category, 0) + 1
        by_sentiment[f.sentiment or "unknown"] = by_sentiment.get(f.sentiment or "unknown", 0) + 1
        by_status[f.status] = by_status.get(f.status, 0) + 1

    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = db.query(models.UserFeedback).filter(
        models.UserFeedback.created_at >= week_ago
    ).count()

    return FeedbackStats(
        total=total,
        avg_rating=avg_rating,
        by_category=by_category,
        by_sentiment=by_sentiment,
        by_status=by_status,
        recent_count=recent_count
    )


@router.get("/all", response_model=List[FeedbackResponse])
def get_all_feedback(
    limit: int = Query(default=50, le=200),
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Admin: get all feedback with optional filters."""
    q = db.query(models.UserFeedback).order_by(models.UserFeedback.created_at.desc())
    if category:
        q = q.filter(models.UserFeedback.category == category)
    if sentiment:
        q = q.filter(models.UserFeedback.sentiment == sentiment)
    return q.limit(limit).all()


@router.patch("/{feedback_id}/status")
def update_feedback_status(
    feedback_id: int,
    status: str = Query(..., regex="^(open|reviewed|resolved)$"),
    db: Session = Depends(get_db)
):
    """Mark a feedback entry as reviewed or resolved."""
    fb = db.query(models.UserFeedback).filter(models.UserFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    fb.status = status
    fb.updated_at = datetime.utcnow()
    db.commit()
    return {"message": f"Feedback {feedback_id} marked as {status}"}
