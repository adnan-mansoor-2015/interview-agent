"""
Simple test script for backend without requiring actual Anthropic API key.
Tests the agent structure and orchestration logic.
"""

print("🧪 Testing Backend Components...")
print()

# Test 1: Config
print("1️⃣ Testing config...")
import config
print(f"   ✅ Config loaded")
print(f"   - Text Model: {config.ANTHROPIC_TEXT_MODEL}")
print(f"   - Vision Model: {config.ANTHROPIC_VISION_MODEL}")
print(f"   - Max Tokens: {config.MAX_TOKENS}")
print()

# Test 2: Session Store (in-memory mode)
print("2️⃣ Testing SessionStore (in-memory)...")
from services.session_store import session_store
test_session_id = session_store.create_session("behavioral", ["Amazon LP"])
print(f"   ✅ Created session: {test_session_id}")
session = session_store.get_session(test_session_id)
print(f"   ✅ Retrieved session: category={session['category']}, phase={session['phase']}")
session_store.add_message(test_session_id, "user", "Test message")
updated_session = session_store.get_session(test_session_id)
print(f"   ✅ Added message: {len(updated_session['conversation_thread'])} messages")
print()

# Test 3: Prompt Generation
print("3️⃣ Testing Prompt Templates...")
from prompts.curator_prompts import get_question_curator_prompt
from prompts.coach_prompts import get_coach_prompt
from prompts.evaluator_prompts import get_evaluator_prompt

curator_prompt = get_question_curator_prompt("behavioral", ["Amazon LP"], [])
print(f"   ✅ Curator prompt generated ({len(curator_prompt)} chars)")

coach_prompt = get_coach_prompt("behavioral", {"question_text": "Test question", "leadership_principle": "Ownership"})
print(f"   ✅ Coach prompt generated ({len(coach_prompt)} chars)")

evaluator_prompt = get_evaluator_prompt("behavioral", {"question_text": "Test"}, [])
print(f"   ✅ Evaluator prompt generated ({len(evaluator_prompt)} chars)")
print()

# Test 4: API Structure
print("4️⃣ Testing FastAPI app structure...")
from app import app
print(f"   ✅ FastAPI app created: {app.title}")
print(f"   ✅ Routes registered:")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ', '.join(route.methods)
        print(f"      - {methods:10} {route.path}")
print()

print("=" * 60)
print("✅ All backend structure tests passed!")
print()
print("⚠️  Note: Actual Claude API calls require ANTHROPIC_API_KEY")
print("   Set your key in .env to test the full flow with real API calls")
print()
print("To start the server:")
print("   uvicorn app:app --reload --port 8000")
print("=" * 60)
