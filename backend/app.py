from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import base64

from services.session_store import session_store
from agents.orchestrator import orchestrator
from agents.evaluator import evaluator

app = FastAPI(title="Interview Prep Agent API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class StartSessionRequest(BaseModel):
    category: str  # behavioral, technical, coding, system-design
    focus_areas: Optional[List[str]] = []


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str


class ImageUploadRequest(BaseModel):
    session_id: str
    image_base64: str
    description: Optional[str] = ""


# Routes
@app.post("/api/chat/start")
def start_session(request: StartSessionRequest):
    """Start a new interview session."""
    try:
        session_id = session_store.create_session(request.category, request.focus_areas)

        # Get first question
        response = orchestrator.process_message(session_id, "Start interview", None)

        return {
            "session_id": session_id,
            "category": request.category,
            "response": response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/message")
def send_message(request: ChatMessageRequest):
    """Send a message in the conversation."""
    try:
        response = orchestrator.process_message(request.session_id, request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/upload")
def upload_diagram(request: ImageUploadRequest):
    """Upload a diagram for system design evaluation."""
    try:
        session = session_store.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session["category"] != "system-design":
            raise HTTPException(status_code=400, detail="Image upload only supported for system design")

        # Evaluate diagram using vision
        evaluation_result = evaluator.evaluate_diagram(
            session["current_question"], request.description, request.image_base64
        )

        if "error" in evaluation_result:
            raise HTTPException(status_code=500, detail=evaluation_result["error"])

        # Format and return
        eval_display = _format_diagram_evaluation(evaluation_result)

        # Add to conversation
        session_store.add_message(request.session_id, "user", f"[Uploaded diagram] {request.description}")
        session_store.add_message(request.session_id, "assistant", eval_display)

        return {"response": {"message": eval_display, "evaluation": evaluation_result}}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    """Get session data including conversation history."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    """Delete a session."""
    session_store.delete_session(session_id)
    return {"message": "Session deleted"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def _format_diagram_evaluation(eval_data: dict):
    """Format diagram evaluation for display."""
    components = eval_data.get("components_identified", [])
    strengths = eval_data.get("strengths", [])
    issues = eval_data.get("critical_issues", [])
    improvements = eval_data.get("suggested_improvements", [])

    output = f"""🔍 **Diagram Analysis**

**Components Identified:**
{chr(10).join(['• ' + c for c in components])}

**Scalability Score:** {eval_data.get('scalability_score', 'N/A')}/10
**Reliability Score:** {eval_data.get('reliability_score', 'N/A')}/10

"""
    if strengths:
        output += "**✅ Strengths:**\n" + "\n".join([f"• {s}" for s in strengths]) + "\n\n"

    if issues:
        output += "**❌ Critical Issues:**\n" + "\n".join([f"• {i}" for i in issues]) + "\n\n"

    if improvements:
        output += "**🔧 Suggested Improvements:**\n" + "\n".join([f"• {i}" for i in improvements])

    return output


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
