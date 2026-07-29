import json
import logging

logger = logging.getLogger("knowledge_engine")

class KnowledgeEngineService:
    @staticmethod
    def enrich_question(question_text: str, subject: str, stage: str) -> dict:
        """
        Retrieves structured knowledge for a given question.
        In a production environment, this would query a knowledge graph or vector DB.
        Here we generate deterministic knowledge mappings for the Government Interview Board.
        """
        if not question_text:
            return {}
            
        # Base lowercase for keyword checking
        q_lower = question_text.lower()
        
        # Current Affairs specific structure
        if stage == "Current Affairs":
            return {
                "title": "Current Affairs Discussion",
                "topic": "Government Policies & Education News",
                "expected_discussion": [
                    "Recent updates in education policy",
                    "Government initiatives (e.g. NEP 2020, NIPUN Bharat)",
                    "Societal impact of current events"
                ],
                "possible_follow_up": [
                    "How would you apply this policy in your classroom?",
                    "What are the challenges in implementing this government initiative?",
                    "How does this impact marginalized students?"
                ],
                "government_relevance": "High - Demonstrates awareness of national educational goals."
            }
            
        # General Subject/Pedagogy Knowledge Mapping
        keywords = []
        expected_concepts = []
        followup_topics = []
        blooms = "Understand"
        difficulty = "medium"
        
        # Heuristic rules to extract knowledge concepts based on the question text
        if "inclusive" in q_lower or "special needs" in q_lower:
            keywords.extend(["inclusive education", "special needs", "equity", "accessibility"])
            expected_concepts.extend(["equal opportunity", "RTE", "learning diversity", "barrier-free environment"])
            followup_topics.extend(["classroom implementation", "teacher responsibility", "assessment adaptation"])
            blooms = "Apply"
            
        elif "technology" in q_lower or "ict" in q_lower:
            keywords.extend(["ICT", "digital literacy", "blended learning"])
            expected_concepts.extend(["integrating tech in pedagogy", "digital divide", "21st century skills"])
            followup_topics.extend(["practical classroom examples", "handling tech failures", "student engagement"])
            blooms = "Create"
            
        elif "manage" in q_lower or "discipline" in q_lower or "behavior" in q_lower:
            keywords.extend(["classroom management", "discipline", "positive reinforcement"])
            expected_concepts.extend(["proactive management", "child psychology", "empathy"])
            followup_topics.extend(["handling disruptive behavior", "parental involvement", "establishing routines"])
            blooms = "Evaluate"
            
        elif "evaluate" in q_lower or "assessment" in q_lower or "test" in q_lower:
            keywords.extend(["formative assessment", "summative assessment", "CCE"])
            expected_concepts.extend(["continuous evaluation", "feedback loop", "holistic development"])
            followup_topics.extend(["designing assessments", "remedial teaching", "peer evaluation"])
            blooms = "Analyze"
            
        else:
            # Generic fallback for unknown topics
            keywords.extend([subject, "pedagogy", "subject fundamentals"])
            expected_concepts.extend(["clear foundational knowledge", "practical application", "student-centric approach"])
            followup_topics.extend(["real-world examples", "teaching methodology", "differentiated instruction"])
            blooms = "Understand"

        return {
            "question": question_text,
            "keywords": keywords,
            "expected_concepts": expected_concepts,
            "followup_topics": followup_topics,
            "difficulty": difficulty,
            "blooms": blooms,
            "government_perspective": "Aligns with NCERT/CBSE pedagogical standards and inclusive national frameworks."
        }
