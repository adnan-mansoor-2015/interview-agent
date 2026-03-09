"""Agent responsible for scoring and providing feedback on answers."""

from __future__ import annotations

from services.claude_client import claude_client
from prompts.evaluator_prompts import get_evaluator_prompt, get_diagram_evaluator_prompt
from question_sources.utils import parse_llm_json


class Evaluator:
    """Scores candidate answers (text and diagram) using the LLM."""

    def evaluate_answer(
        self,
        category: str,
        question_data: dict,
        conversation_thread: list[dict],
    ) -> dict:
        """Evaluate a complete answer and return structured feedback."""
        try:
            system_prompt = get_evaluator_prompt(category, question_data, conversation_thread)

            response = claude_client.send_message(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": "Evaluate the candidate's full response."}],
            )

            return parse_llm_json(claude_client.extract_text(response))

        except Exception as e:
            return {"error": f"Evaluation failed: {str(e)}"}

    def evaluate_diagram(
        self,
        question_data: dict,
        user_description: str,
        image_base64: str,
    ) -> dict:
        """Evaluate a system design diagram using vision."""
        try:
            system_prompt = get_diagram_evaluator_prompt(question_data, user_description)

            response = claude_client.send_message_with_image(
                system_prompt=system_prompt,
                text="Evaluate this system design diagram based on the question requirements.",
                image_base64=image_base64,
            )

            return parse_llm_json(claude_client.extract_text(response))

        except Exception as e:
            return {"error": f"Diagram evaluation failed: {str(e)}"}


# Global instance
evaluator = Evaluator()
