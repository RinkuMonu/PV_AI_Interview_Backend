from pydantic import BaseModel

class QuestionRankingScore(BaseModel):
    difficulty_match: float = 1.0
    topic_priority: float = 1.0
    weak_topic_priority: float = 1.0
    similarity_score: float = 1.0
    popularity: float = 1.0
    coverage_score: float = 1.0
    recency_penalty: float = 1.0
    randomness_factor: float = 1.0
    duplicate_penalty: float = 1.0
    
    @property
    def final_score(self) -> float:
        # A simple linear combination (can be made configurable later)
        return (self.difficulty_match * 0.2 +
                self.topic_priority * 0.2 +
                self.weak_topic_priority * 0.2 +
                self.similarity_score * 0.1 +
                self.popularity * 0.05 +
                self.coverage_score * 0.1 +
                self.recency_penalty * 0.05 +
                self.randomness_factor * 0.05) * self.duplicate_penalty
