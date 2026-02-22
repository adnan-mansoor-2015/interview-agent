import json
from services.claude_client import claude_client
from prompts.evaluator_prompts import get_evaluator_prompt, get_diagram_evaluator_prompt


class Evaluator:
    """Agent responsible for scoring and providing feedback on answers."""

    def evaluate_answer(self, category: str, question_data: dict, conversation_thread: list):
        """Evaluate a complete answer and return structured feedback."""
        try:
            system_prompt = get_evaluator_prompt(category, question_data, conversation_thread)

            response = claude_client.send_message(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": "Evaluate the candidate's full response."}],
            )

            content = claude_client.extract_text(response)

            # Parse JSON evaluation
            evaluation = self._parse_json(content)

            return evaluation

        except Exception as e:
            return {"error": f"Evaluation failed: {str(e)}"}

    def evaluate_diagram(self, question_data: dict, user_description: str, image_base64: str):
        """Evaluate a system design diagram using vision."""
        try:
            system_prompt = get_diagram_evaluator_prompt(question_data, user_description)

            response = claude_client.send_message_with_image(
                system_prompt=system_prompt,
                text="Evaluate this system design diagram based on the question requirements.",
                image_base64=image_base64,
            )

            content = claude_client.extract_text(response)

            # Parse JSON evaluation
            evaluation = self._parse_json(content)

            return evaluation

        except Exception as e:
            return {"error": f"Diagram evaluation failed: {str(e)}"}

    def _parse_json(self, content: str):
        """Extract and parse JSON from Claude's response."""
        # Strip markdown code fences
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)


# Global instance
evaluator = Evaluator()
