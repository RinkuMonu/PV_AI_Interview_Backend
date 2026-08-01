from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.services.budget_manager import BudgetManager

router = APIRouter()

def get_budget_manager() -> BudgetManager:
    return BudgetManager()

@router.get("/{interview_id}")
async def get_budget(interview_id: str, manager: BudgetManager = Depends(get_budget_manager)):
    budget = await manager.get_budget_status(interview_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget.model_dump()

@router.get("/status/{interview_id}")
async def get_budget_status(interview_id: str, manager: BudgetManager = Depends(get_budget_manager)):
    budget = await manager.get_budget_status(interview_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget.status.model_dump()

@router.get("/usage/{interview_id}")
async def get_budget_usage(interview_id: str, manager: BudgetManager = Depends(get_budget_manager)):
    budget = await manager.get_budget_status(interview_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget.usage.model_dump()

@router.get("/cost/{interview_id}")
async def get_budget_cost(interview_id: str, manager: BudgetManager = Depends(get_budget_manager)):
    budget = await manager.get_budget_status(interview_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    return {
        "interview_id": interview_id,
        "total_cost": budget.usage.total_cost,
        "max_cost": budget.budget.max_cost,
        "remaining_cost": manager.remaining_cost(budget),
        "budget_level": budget.status.budget_level
    }
