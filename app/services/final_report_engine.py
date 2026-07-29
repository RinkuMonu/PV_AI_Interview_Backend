import json
from app.services.live_question_generator import LiveQuestionGeneratorService

class FinalReportEngine:
    @staticmethod
    async def generate_final_report(
        interview_id: str,
        exam: str,
        subject: str,
        experience_level: str,
        conversation_history: list,
        candidate_summary: dict
    ) -> dict:
        """
        Generates a comprehensive final government interview report using LLM.
        """
        
        # Calculate base statistics from python directly
        questions_asked = 0
        candidate_turns = 0
        total_candidate_words = 0
        follow_ups_asked = 0
        
        transcript = ""
        for turn in conversation_history:
            role = turn.get("role", "")
            content = turn.get("content", "")
            
            transcript += f"{role.capitalize()}: {content}\n\n"
            
            if role in ["interviewer", "assistant"]:
                questions_asked += 1
                if turn.get("topic") == "Follow-up" or turn.get("asked_follow_up"):
                    follow_ups_asked += 1
            elif role in ["candidate", "user"]:
                candidate_turns += 1
                total_candidate_words += len(content.split())
                
        average_response_length = (total_candidate_words // max(candidate_turns, 1))
        
        topics_covered = candidate_summary.get("topics_discussed", [])
        mastered = candidate_summary.get("topics_mastered", [])
        revision = candidate_summary.get("topics_needing_revision", [])
        
        strongest_topic = mastered[0] if mastered else (topics_covered[0] if topics_covered else "General")
        weakest_topic = revision[0] if revision else (topics_covered[-1] if topics_covered else "General")
        
        avg_score = candidate_summary.get("average_score", 0)
        # Scale the 0-10 score to a 0-100 scale for the report rating
        overall_score_100 = min(max(int(avg_score * 10), 0), 100)
        
        if overall_score_100 >= 90:
            rating = "Outstanding"
        elif overall_score_100 >= 80:
            rating = "Very Good"
        elif overall_score_100 >= 70:
            rating = "Good"
        elif overall_score_100 >= 60:
            rating = "Average"
        else:
            rating = "Needs Improvement"
            
        system_prompt = f"""You are a strict Government Exam Interview Panel Assessor.
Your task is to review the following interview transcript and generate a realistic, personalized final evaluation report.

Exam Details:
- Exam: {exam}
- Subject: {subject}
- Experience Level: {experience_level}

Candidate Summary context (from heuristics):
{json.dumps(candidate_summary, indent=2)}

You must evaluate the candidate on the following 10 categories, giving each a score out of 10, plus strengths, weaknesses, and recommendations:
1. Subject Knowledge
2. Conceptual Understanding
3. Practical Application
4. Classroom Management
5. Communication Skills
6. Confidence
7. Logical Thinking
8. Government Awareness
9. Behaviour & Professionalism
10. Overall Interview Performance

Feedback Rules:
- DO NOT use generic statements. Reference specific answers given by the candidate in the transcript.
- Identify specific strong and weak topics.

Return the response STRICTLY as a JSON object matching this exact schema:
{{
    "categories": [
        {{
            "name": "Subject Knowledge",
            "score": 8.5,
            "strengths": ["..."],
            "weaknesses": ["..."],
            "recommendations": ["..."]
        }}
        // Include exactly all 10 categories
    ],
    "overall_summary": {{
        "overall_rating": "{rating}",
        "interview_level": "{experience_level}",
        "readiness": "string (e.g. Highly Ready, Needs Practice)",
        "recommended_preparation_areas": ["..."],
        "top_5_strengths": ["..."],
        "top_5_weaknesses": ["..."]
    }},
    "statistics": {{
        "questions_asked": {questions_asked},
        "follow_ups_asked": {follow_ups_asked},
        "topics_covered": {json.dumps(topics_covered)},
        "average_response_length_words": {average_response_length},
        "strongest_topic": "{strongest_topic}",
        "weakest_topic": "{weakest_topic}",
        "average_score_out_of_100": {overall_score_100},
        "interview_duration": "Completed"
    }}
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Here is the interview transcript:\n\n" + transcript}
        ]
        
        try:
            report_json = await LiveQuestionGeneratorService.generate_json_response(messages)
            return report_json
        except Exception as e:
            import logging
            logging.error(f"Failed to generate final report: {e}")
            # Return a fallback safe JSON structure if LLM fails
            return {
                "categories": [],
                "overall_summary": {
                    "overall_rating": rating,
                    "interview_level": experience_level,
                    "readiness": "Unknown",
                    "recommended_preparation_areas": [],
                    "top_5_strengths": [],
                    "top_5_weaknesses": []
                },
                "statistics": {
                    "questions_asked": questions_asked,
                    "follow_ups_asked": follow_ups_asked,
                    "topics_covered": topics_covered,
                    "average_response_length_words": average_response_length,
                    "strongest_topic": strongest_topic,
                    "weakest_topic": weakest_topic,
                    "average_score_out_of_100": overall_score_100,
                    "interview_duration": "Completed"
                }
            }
