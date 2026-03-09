"""Interview coach agent — asks follow-up questions like a real interviewer.

The coach reviews the conversation so far and either asks a short
follow-up probing for depth, or responds with ``COMPLETE`` when
the candidate has adequately covered the topic.
"""

from __future__ import annotations

from services.claude_client import claude_client
from prompts.coach_prompts import get_coach_prompt


class InterviewCoach:
    """Asks follow-up questions and decides when an answer is complete."""

    def process_answer(
        self,
        category: str,
        question_data: dict,
        conversation_thread: list[dict[str, str]],
    ) -> str:
        """Return a follow-up question or ``'COMPLETE'``."""
        try:
            system_prompt = get_coach_prompt(category, question_data)
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_thread]
            response = claude_client.send_message(system_prompt=system_prompt, messages=messages)
            return claude_client.extract_text(response).strip()
        except Exception as e:
            return f"Error: {str(e)}"


# Global instance
interview_coach = InterviewCoach()
