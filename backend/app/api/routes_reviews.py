from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from backend.app.db.database import get_connection
from backend.app.models.schemas import (
    EntitlementReviewItem, DecisionSubmission, ReviewDecisionRecord, BulkDecisionSubmission
)
from backend.app.services.review_service import ReviewService

router = APIRouter(prefix="/api/reviews", tags=["Access Reviews"])
review_service = ReviewService()

@router.get("/items", response_model=List[EntitlementReviewItem])
def get_review_items(
    mode: str = Query("prototype", description="Review mode: 'baseline' or 'prototype'"),
    department: Optional[str] = Query(None, description="Filter by department")
):
    if mode not in ["baseline", "prototype"]:
        raise HTTPException(status_code=400, detail="Mode must be 'baseline' or 'prototype'")
    
    conn = get_connection()
    try:
        return review_service.get_review_items(conn, mode=mode, department_filter=department)
    finally:
        conn.close()

@router.post("/decision", response_model=ReviewDecisionRecord)
def submit_decision(submission: DecisionSubmission):
    conn = get_connection()
    try:
        return review_service.submit_decision(conn, submission)
    finally:
        conn.close()

@router.post("/bulk-baseline", response_model=List[ReviewDecisionRecord])
def bulk_submit_baseline(bulk: BulkDecisionSubmission):
    conn = get_connection()
    try:
        return review_service.bulk_submit_baseline(conn, bulk)
    finally:
        conn.close()
