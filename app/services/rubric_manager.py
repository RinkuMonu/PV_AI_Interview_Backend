from typing import Dict, Optional
from app.services.evaluation_repository import EvaluationRepository
from app.schemas.rubric import Rubric, EvaluationProfile
from app.models.evaluation_models import InterviewProfileType

class RubricManager:
    def __init__(self, repo: EvaluationRepository = None):
        self.repo = repo or EvaluationRepository()

    async def get_rubric(self, rubric_id: str) -> Optional[Rubric]:
        return await self.repo.get_rubric(rubric_id)

    async def save_rubric(self, rubric: Rubric):
        await self.repo.save_rubric(rubric)

    async def get_profile(self, profile_type: InterviewProfileType) -> EvaluationProfile:
        profile = await self.repo.get_profile(profile_type)
        if not profile:
            # Fallback mock for testing
            profile = EvaluationProfile(
                profile_id="default_profile",
                type=profile_type,
                prompt_template_id="template_001",
                rubric_id="default_rubric",
                competencies=["Technical", "Communication", "Reasoning"],
                scoring_weights={"technical": 0.4, "communication": 0.3, "reasoning": 0.3},
                pass_criteria="overall_score >= 60"
            )
        return profile
