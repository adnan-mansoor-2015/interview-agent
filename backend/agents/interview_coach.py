from services.claude_client import claude_client
from prompts.coach_prompts import get_coach_prompt


class InterviewCoach:
    """Agent responsible for asking follow-up questions and guiding the interview."""

    def process_answer(self, category: str, question_data: dict, conversation_thread: list):
        """Assess answer completeness and provide follow-up or mark complete."""
        try:
            system_prompt = get_coach_prompt(category, question_data)

            # Build conversation for Claude
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_thread]

            response = claude_client.send_message(system_prompt=system_prompt, messages=messages)

            return claude_client.extract_text(response).strip()

        except Exception as e:
            return f"Error: {str(e)}"


# Global instance
interview_coach = InterviewCoach()
