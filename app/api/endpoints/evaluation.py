from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from app.schemas.evaluation import EvaluationRecord
from app.schemas.competency import CompetencyProfile
from app.schemas.rubric import Rubric, EvaluationProfile
from app.models.evaluation_models import InterviewProfileType
from app.services.evaluation_engine import EvaluationEngine
from app.services.evaluation_repository import EvaluationRepository
from app.services.rubric_manager import RubricManager
from app.services.competency_manager import CompetencyManager
from app.services.report_generator import ReportGenerator
from app.schemas.report import Report
from app.core.events import event_bus

router = APIRouter()
evaluation_engine = EvaluationEngine()
repo = EvaluationRepository()
rubric_manager = RubricManager()
competency_manager = CompetencyManager()
report_generator = ReportGenerator()

class AnswerRequest(BaseModel):
    interview_id: str
    candidate_id: str
    question_id: str
    question: str
    candidate_answer: str
    expected_answer: str = None
    profile_type: InterviewProfileType

@router.post("/answer", response_model=EvaluationRecord)
async def evaluate_answer(req: AnswerRequest):
    try:
        record = await evaluation_engine.evaluate_answer(
            interview_id=req.interview_id,
            candidate_id=req.candidate_id,
            question_id=req.question_id,
            question=req.question,
            candidate_answer=req.candidate_answer,
            expected_answer=req.expected_answer,
            profile_type=req.profile_type
        )
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}", response_model=EvaluationRecord)
async def get_evaluation(id: str):
    record = await repo.get_evaluation(id)
    if not record:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return record

@router.get("/interview/{interview_id}", response_model=List[EvaluationRecord])
async def get_interview_evaluations(interview_id: str):
    return await repo.get_interview_evaluations(interview_id)

@router.get("/competency/{candidate_id}", response_model=CompetencyProfile)
async def get_competency(candidate_id: str, subject: str = "General"):
    profile = await competency_manager.get_profile(candidate_id, subject)
    if not profile:
        raise HTTPException(status_code=404, detail="Competency profile not found")
    return profile

@router.get("/rubrics/{rubric_id}", response_model=Rubric)
async def get_rubric(rubric_id: str):
    rubric = await rubric_manager.get_rubric(rubric_id)
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return rubric

@router.post("/rubrics")
async def create_rubric(rubric: Rubric):
    await rubric_manager.save_rubric(rubric)
    return {"status": "success"}

@router.post("/report/{interview_id}", response_model=Report)
async def generate_report(interview_id: str, candidate_id: str):
    evaluations = await repo.get_interview_evaluations(interview_id)
    if not evaluations:
        raise HTTPException(status_code=404, detail="No evaluations found for this interview")
        
    overall_sum = sum(e.scorecard.overall_score for e in evaluations)
    overall_avg = overall_sum / len(evaluations)
    passed = overall_avg >= 60.0
    
    report = report_generator.generate(
        candidate_id=candidate_id,
        interview_id=interview_id,
        evaluations=evaluations,
        overall_score=overall_avg,
        passed=passed
    )
    
    await event_bus.publish("report_generated", {"interview_id": interview_id})
    return report

@router.put("/rubrics/{rubric_id}")
async def update_rubric(rubric_id: str, rubric: Rubric):
    if rubric_id != rubric.rubric_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    await rubric_manager.save_rubric(rubric)
    return {"status": "success"}
