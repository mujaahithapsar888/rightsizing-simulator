"""
feedback.py
────────────
API Router for saving and retrieving stakeholder rating feedback.
Allows rating: Ease of Use, Recommendation Quality, Trust, and Overall Satisfaction.
Stores feedback in memory for fast performance, recalculating average ratings.
"""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

class FeedbackPayload(BaseModel):
    ease_of_use: int = Field(..., ge=1, le=5)
    recommendation_quality: int = Field(..., ge=1, le=5)
    trust: int = Field(..., ge=1, le=5)
    overall_satisfaction: int = Field(..., ge=1, le=5)
    comments: str = ""

# In-memory storage for feedback ratings
FEEDBACK_STORE: List[Dict[str, Any]] = [
    {"ease_of_use": 4, "recommendation_quality": 5, "trust": 4, "overall_satisfaction": 5, "comments": "Excellent SLA compliance matching."},
    {"ease_of_use": 5, "recommendation_quality": 4, "trust": 5, "overall_satisfaction": 4, "comments": "The multi-candidate optimizer is very stable."},
]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackPayload,
    current_user: User = Depends(get_current_user),
):
    FEEDBACK_STORE.append(payload.model_dump())
    return {"status": "success", "message": "Feedback submitted successfully."}

@router.get("/")
async def get_feedback_averages(
    current_user: User = Depends(get_current_user),
):
    if not FEEDBACK_STORE:
        return {
            "avg_ease_of_use": 0.0,
            "avg_recommendation_quality": 0.0,
            "avg_trust": 0.0,
            "avg_overall_satisfaction": 0.0,
            "total_reviews": 0
        }
    
    eou = [f["ease_of_use"] for f in FEEDBACK_STORE]
    rq = [f["recommendation_quality"] for f in FEEDBACK_STORE]
    tr = [f["trust"] for f in FEEDBACK_STORE]
    os = [f["overall_satisfaction"] for f in FEEDBACK_STORE]

    return {
        "avg_ease_of_use": round(sum(eou) / len(eou), 2),
        "avg_recommendation_quality": round(sum(rq) / len(rq), 2),
        "avg_trust": round(sum(tr) / len(tr), 2),
        "avg_overall_satisfaction": round(sum(os) / len(os), 2),
        "total_reviews": len(FEEDBACK_STORE),
        "comments": [f["comments"] for f in FEEDBACK_STORE if f.get("comments")]
    }
