import json
from services.session_store import session_store
from agents.question_curator import question_curator
from agents.interview_coach import interview_coach
from agents.evaluator import evaluator


class Orchestrator:
    """Main agent that routes between specialized agents based on session phase."""

    def process_message(self, session_id: str, user_message: str, image_base64: str = None):
        """Process user message and route to appropriate agent."""
        session = session_store.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        phase = session["phase"]
        category = session["category"]

        # Phase: Need a new question
        if phase == "question_needed" or user_message.lower() in ["next", "next question", "skip"]:
            return self._handle_new_question(session_id, session)

        # Phase: User is answering
        elif phase == "answering":
            # Add user message to thread
            session_store.add_message(session_id, "user", user_message)

            # Check if user requested evaluation
            if "evaluate" in user_message.lower() or user_message.lower() == "eval":
                session_store.set_phase(session_id, "evaluating")
                return self._handle_evaluation(session_id, session)

            # Otherwise, coach provides follow-up or marks complete
            coach_response = interview_coach.process_answer(
                category, session["current_question"], session["conversation_thread"]
            )

            # Check if coach says complete
            if coach_response.strip().upper() == "COMPLETE":
                session_store.set_phase(session_id, "ready_for_eval")
                session_store.add_message(
                    session_id,
                    "assistant",
                    "Okay, I think that covers it. Whenever you're ready, hit Evaluate and I'll give you my feedback.",
                )
                return {
                    "message": "Okay, I think that covers it. Whenever you're ready, hit Evaluate and I'll give you my feedback.",
                    "phase": "ready_for_eval",
                    "show_evaluate_button": True,
                }
            else:
                # Coach asked a follow-up
                session_store.add_message(session_id, "assistant", coach_response)
                return {"message": coach_response, "phase": "answering"}

        # Phase: Ready for evaluation (user clicked evaluate button)
        elif phase == "ready_for_eval" or phase == "evaluating":
            return self._handle_evaluation(session_id, session)

        else:
            return {"error": "Unknown phase"}

    def _handle_new_question(self, session_id: str, session: dict):
        """Get a new question from Question Curator."""
        question_data = question_curator.get_question(
            session["category"], session["focus_areas"], session["asked_questions"]
        )

        if "error" in question_data:
            error_msg = f"⚠️ Could not load question: {question_data['error']}"
            session_store.add_message(session_id, "assistant", error_msg)
            return {"message": error_msg, "phase": "question_needed", "show_next_button": True}

        # Update session
        session["current_question"] = question_data
        session["conversation_thread"] = []
        session["phase"] = "answering"
        session_store.update_session(session_id, session)
        session_store.add_asked_question(session_id, question_data["question_id"])

        # Format question display
        question_display = self._format_question(question_data, session["category"])
        session_store.add_message(session_id, "assistant", question_display)

        return {
            "message": question_display,
            "question_data": question_data,
            "phase": "answering",
        }

    def _handle_evaluation(self, session_id: str, session: dict):
        """Get evaluation from Evaluator Agent."""
        evaluation_result = evaluator.evaluate_answer(
            session["category"], session["current_question"], session["conversation_thread"]
        )

        if "error" in evaluation_result:
            return evaluation_result

        # Store evaluation
        session["evaluations"].append(
            {"question_id": session["current_question"]["question_id"], "evaluation": evaluation_result}
        )
        session["phase"] = "question_needed"
        session_store.update_session(session_id, session)

        # Format evaluation display
        eval_display = self._format_evaluation(evaluation_result)
        session_store.add_message(session_id, "assistant", eval_display)

        return {
            "message": eval_display,
            "evaluation": evaluation_result,
            "phase": "question_needed",
            "show_next_button": True,
        }

    def _format_question(self, question_data: dict, category: str):
        """Format question for display — keep it short like a real interviewer."""
        if category == "coding":
            return f"""Alright, let's do a coding problem.

**{question_data.get('question_title')}** ({question_data.get('difficulty')})

{question_data.get('leetcode_url')}

Take a look and walk me through your approach."""

        elif category == "system-design":
            return f"""Okay, let's do a design question.

{question_data.get('question_text')}

Assume we're dealing with {question_data.get('scale_requirements', 'large scale')}. Where would you start?"""

        elif category == "behavioral":
            return f"""{question_data.get('question_text')}"""

        else:  # technical
            return f"""{question_data.get('question_text')}"""

    def _format_evaluation(self, eval_data: dict):
        """Format evaluation for display."""
        score = eval_data.get("overall_score", 0)
        score_emoji = "🎉" if score >= 7 else "👍" if score >= 5 else "📈"

        strengths = eval_data.get("strengths", [])
        improvements = eval_data.get("improvements", [])

        output = f"""📊 **Evaluation Results** {score_emoji}

**Overall Score: {score}/10**

"""
        if strengths:
            output += "**💪 Strengths:**\n" + "\n".join([f"• {s}" for s in strengths]) + "\n\n"

        if improvements:
            output += "**📈 Areas for Improvement:**\n" + "\n".join([f"• {i}" for i in improvements]) + "\n\n"

        follow_ups = eval_data.get("follow_up_questions", [])
        if follow_ups:
            output += "**🔍 Follow-up Questions an Interviewer Might Ask:**\n" + "\n".join(
                [f"• {q}" for q in follow_ups]
            )

        return output


# Global orchestrator instance
orchestrator = Orchestrator()
