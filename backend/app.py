"""FastAPI application — interview prep agent REST API."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.session_store import session_store
from services.progress_store import progress_store
from agents.orchestrator import orchestrator
from agents.evaluator import evaluator
from agents.question_curator import question_curator

app = FastAPI(title="Interview Prep Agent API")

# ── CORS ────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ──────────────────────────────────────


class StartSessionRequest(BaseModel):
    """Body for ``POST /api/chat/start``."""
    category: str
    focus_areas: list[str] | None = []
    user_email: str | None = ""


class ChatMessageRequest(BaseModel):
    """Body for ``POST /api/chat/message``."""
    session_id: str
    message: str


class ImageUploadRequest(BaseModel):
    """Body for ``POST /api/chat/upload``."""
    session_id: str
    image_base64: str
    description: str | None = ""


class UpdateFocusRequest(BaseModel):
    """Body for ``PUT /api/session/{id}/focus``."""
    focus_areas: list[str]


class MessageResponse(BaseModel):
    """Generic envelope returned by most endpoints."""
    message: str


class HealthResponse(BaseModel):
    """Response for ``GET /health``."""
    status: str


# ── Routes ──────────────────────────────────────────────────────────


@app.post("/api/chat/start")
def start_session(request: StartSessionRequest) -> dict[str, Any]:
    """Start a new interview session."""
    try:
        session_id = session_store.create_session(
            request.category, request.focus_areas, request.user_email
        )
        response = orchestrator.process_message(session_id, "Start interview", None)
        return {"session_id": session_id, "category": request.category, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/message")
def send_message(request: ChatMessageRequest) -> dict[str, Any]:
    """Send a message in the conversation."""
    try:
        response = orchestrator.process_message(request.session_id, request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/upload")
def upload_diagram(request: ImageUploadRequest) -> dict[str, Any]:
    """Upload a diagram for system design evaluation."""
    try:
        session = session_store.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session["category"] != "system-design":
            raise HTTPException(status_code=400, detail="Image upload only supported for system design")

        evaluation_result = evaluator.evaluate_diagram(
            session["current_question"], request.description, request.image_base64
        )

        if "error" in evaluation_result:
            raise HTTPException(status_code=500, detail=evaluation_result["error"])

        eval_display = _format_diagram_evaluation(evaluation_result)
        session_store.add_message(request.session_id, "user", f"[Uploaded diagram] {request.description}")
        session_store.add_message(request.session_id, "assistant", eval_display)

        return {"response": {"message": eval_display, "evaluation": evaluation_result}}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    """Get session data including conversation history."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    """Delete a session."""
    session_store.delete_session(session_id)
    return {"message": "Session deleted"}


@app.get("/api/categories/{category}/structure")
def get_category_structure(category: str) -> dict[str, Any]:
    """Return hierarchy tree with question counts for dropdown navigation."""
    structure = question_curator.get_category_structure(category)
    if not structure:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
    return {"category": category, "structure": structure}


@app.put("/api/session/{session_id}/focus")
def update_focus_areas(session_id: str, request: UpdateFocusRequest) -> dict[str, Any]:
    """Update focus areas mid-session for subtopic switching."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["focus_areas"] = request.focus_areas
    session_store.update_session(session_id, session)
    return {"message": "Focus areas updated", "focus_areas": request.focus_areas}


@app.get("/api/session/{session_id}/progress")
def get_session_progress(session_id: str) -> dict[str, Any]:
    """Return coverage stats at every hierarchy level."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    progress = question_curator.get_progress(session["category"], session["asked_questions"])
    return {"category": session["category"], "progress": progress}


@app.get("/api/session/{session_id}/progress/detailed")
def get_detailed_progress(session_id: str) -> dict[str, Any]:
    """Return full topic tree with per-item completion status."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    progress = question_curator.get_detailed_progress(session["category"], session["asked_questions"])
    return {"category": session["category"], "progress": progress}


@app.get("/api/progress/{category}")
def get_persistent_progress(category: str, user_email: str = "") -> dict[str, Any]:
    """Return progress from persistent store (no session needed)."""
    asked = progress_store.get_asked_questions(user_email, category)
    progress = question_curator.get_progress(category, asked)
    return {"category": category, "progress": progress}


@app.get("/api/progress/{category}/detailed")
def get_persistent_detailed_progress(category: str, user_email: str = "") -> dict[str, Any]:
    """Return detailed progress from persistent store (no session needed)."""
    asked = progress_store.get_asked_questions(user_email, category)
    progress = question_curator.get_detailed_progress(category, asked)
    return {"category": category, "progress": progress}


@app.delete("/api/progress/{category}")
def reset_progress(category: str, user_email: str = "") -> dict[str, str]:
    """Reset persistent progress for a category."""
    progress_store.reset(user_email, category)
    return {"message": f"Progress reset for {category}"}


@app.delete("/api/progress")
def reset_all_progress(user_email: str = "") -> dict[str, str]:
    """Reset all persistent progress for a user."""
    progress_store.reset(user_email)
    return {"message": "All progress reset"}


@app.get("/health")
def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy")


# ── Helpers ─────────────────────────────────────────────────────────


def _format_diagram_evaluation(eval_data: dict[str, Any]) -> str:
    """Format diagram evaluation for display."""
    components = eval_data.get("components_identified", [])
    strengths = eval_data.get("strengths", [])
    issues = eval_data.get("critical_issues", [])
    improvements = eval_data.get("suggested_improvements", [])

    parts: list[str] = [
        "🔍 **Diagram Analysis**\n\n"
        f"**Components Identified:**\n"
        + "\n".join(f"• {c}" for c in components)
        + f"\n\n**Scalability Score:** {eval_data.get('scalability_score', 'N/A')}/10"
        + f"\n**Reliability Score:** {eval_data.get('reliability_score', 'N/A')}/10"
    ]

    if strengths:
        parts.append("**✅ Strengths:**\n" + "\n".join(f"• {s}" for s in strengths))
    if issues:
        parts.append("**❌ Critical Issues:**\n" + "\n".join(f"• {i}" for i in issues))
    if improvements:
        parts.append("**🔧 Suggested Improvements:**\n" + "\n".join(f"• {i}" for i in improvements))

    return "\n\n".join(parts)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
