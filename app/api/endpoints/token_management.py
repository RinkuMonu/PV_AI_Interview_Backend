from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.services.token_manager import TokenManager, get_token_manager

router = APIRouter()

@router.get("/interview/{interview_id}")
async def get_interview_usage(interview_id: str, manager: TokenManager = Depends(get_token_manager)):
    """
    Get aggregated token usage and estimated cost for a specific interview session.
    """
    usage = await manager.get_interview_usage(interview_id)
    if not usage:
        raise HTTPException(status_code=404, detail="No token usage found for this interview")
    return usage

@router.get("/candidate/{candidate_id}")
async def get_candidate_usage(candidate_id: str, manager: TokenManager = Depends(get_token_manager)):
    """
    Get aggregated token usage and estimated cost across all interviews for a specific candidate.
    """
    usage = await manager.get_candidate_usage(candidate_id)
    if not usage:
        raise HTTPException(status_code=404, detail="No token usage found for this candidate")
    return usage
