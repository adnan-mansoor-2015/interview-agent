"""Central orchestrator — routes messages between the specialised agents.

The session moves through phases:

  ``question_needed`` → ``answering`` → ``ready_for_eval`` → ``evaluating``
                                    ↘  (user says "evaluate") → ``evaluating``

After evaluation the phase resets to ``question_needed``.
"""

from __future__ import annotations

from typing import Any

from services.session_store import session_store
from services.progress_store import progress_store
from agents.question_curator import question_curator
from agents.interview_coach import interview_coach
from agents.evaluator import evaluator


class Orchestrator:
    """Routes user messages to the appropriate agent based on session phase."""

    def process_message(
        self,
        session_id: str,
        user_message: str,
        image_base64: str | None = None,
    ) -> dict[str, Any]:
        """Process a user message and return the agent's response."""
        session = session_store.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        phase = session["phase"]

        # Phase: Need a new question
        if phase == "question_needed" or user_message.lower() in ["next", "next question", "skip"]:
            return self._handle_new_question(session_id, session)

        # Phase: User is answering
        elif phase == "answering":
            session_store.add_message(session_id, "user", user_message)

            # Check if user requested evaluation
            if "evaluate" in user_message.lower() or user_message.lower() == "eval":
                session_store.set_phase(session_id, "evaluating")
                return self._handle_evaluation(session_id, session)

            # Otherwise, coach provides follow-up or marks complete
            coach_response = interview_coach.process_answer(
                session["category"], session["current_question"], session["conversation_thread"]
            )

            if coach_response.strip().upper() == "COMPLETE":
                session_store.set_phase(session_id, "ready_for_eval")
                msg = "Okay, I think that covers it. Whenever you're ready, hit Evaluate and I'll give you my feedback."
                session_store.add_message(session_id, "assistant", msg)
                return {
                    "message": msg,
                    "phase": "ready_for_eval",
                    "show_evaluate_button": True,
                }
            else:
                session_store.add_message(session_id, "assistant", coach_response)
                return {"message": coach_response, "phase": "answering"}

        # Phase: Ready for evaluation
        elif phase in ("ready_for_eval", "evaluating"):
            return self._handle_evaluation(session_id, session)

        else:
            return {"error": "Unknown phase"}

    # ── Private helpers ─────────────────────────────────────────────

    def _handle_new_question(self, session_id: str, session: dict[str, Any]) -> dict[str, Any]:
        """Fetch a new question from the Question Curator."""
        question_data = question_curator.get_question(
            session["category"], session["focus_areas"], session["asked_questions"]
        )

        if "error" in question_data:
            error_msg = f"Could not load question: {question_data['error']}"
            session_store.add_message(session_id, "assistant", error_msg)
            return {"message": error_msg, "phase": "question_needed", "show_next_button": True}

        # Update session
        session["current_question"] = question_data
        session["conversation_thread"] = []
        session["phase"] = "answering"
        session_store.update_session(session_id, session)
        session_store.add_asked_question(session_id, question_data["question_id"])
        progress_store.add_asked_question(
            session.get("user_email", ""), session["category"], question_data["question_id"]
        )

        question_display = self._format_question(question_data, session["category"])
        session_store.add_message(session_id, "assistant", question_display)

        return {
            "message": question_display,
            "question_data": question_data,
            "phase": "answering",
        }

    def _handle_evaluation(self, session_id: str, session: dict[str, Any]) -> dict[str, Any]:
        """Run the Evaluator agent and return formatted feedback."""
        evaluation_result = evaluator.evaluate_answer(
            session["category"], session["current_question"], session["conversation_thread"]
        )

        if "error" in evaluation_result:
            return evaluation_result

        session["evaluations"].append(
            {"question_id": session["current_question"]["question_id"], "evaluation": evaluation_result}
        )
        session["phase"] = "question_needed"
        session_store.update_session(session_id, session)

        eval_display = self._format_evaluation(evaluation_result)
        session_store.add_message(session_id, "assistant", eval_display)

        return {
            "message": eval_display,
            "evaluation": evaluation_result,
            "phase": "question_needed",
            "show_next_button": True,
        }

    def _format_question(self, question_data: dict[str, Any], category: str) -> str:
        """Format a question for display — short and conversational."""
        if category == "coding":
            return (
                f"Alright, let's do a coding problem.\n\n"
                f"**{question_data.get('question_title')}** ({question_data.get('difficulty')})\n\n"
                f"{question_data.get('leetcode_url')}\n\n"
                f"Take a look and walk me through your approach."
            )
        elif category == "system-design":
            return (
                f"Okay, let's do a design question.\n\n"
                f"{question_data.get('question_text')}\n\n"
                f"Assume we're dealing with {question_data.get('scale_requirements', 'large scale')}. "
                f"Where would you start?"
            )
        else:
            # behavioral & technical — question text is enough
            return question_data.get("question_text", "")

    def _format_evaluation(self, eval_data: dict[str, Any]) -> str:
        """Format evaluation results for display."""
        score: int = eval_data.get("overall_score", 0)
        emoji = "🎉" if score >= 7 else "👍" if score >= 5 else "📈"

        parts: list[str] = [f"📊 **Evaluation Results** {emoji}\n\n**Overall Score: {score}/10**\n"]

        strengths = eval_data.get("strengths", [])
        if strengths:
            parts.append("**💪 Strengths:**\n" + "\n".join(f"• {s}" for s in strengths))

        improvements = eval_data.get("improvements", [])
        if improvements:
            parts.append("**📈 Areas for Improvement:**\n" + "\n".join(f"• {i}" for i in improvements))

        follow_ups = eval_data.get("follow_up_questions", [])
        if follow_ups:
            parts.append("**🔍 Follow-up Questions an Interviewer Might Ask:**\n" + "\n".join(f"• {q}" for q in follow_ups))

        return "\n\n".join(parts)


# Global orchestrator instance
orchestrator = Orchestrator()
