import os
import requests
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk import Agent

# --- Configuration Constants ---
DEFAULT_AGENT_NAME = "Orchestrator Agent"
HEALTH_STATUS_OK = "healthy"
PROFILER_URL = os.environ.get("PROFILER_URL", "http://profiler-service:8080")
WEALTH_ADVISOR_URL = os.environ.get("WEALTH_ADVISOR_URL", "http://localhost:8002")

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title=DEFAULT_AGENT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# UI Mount moved to bottom so API routes take precedence

AGENT_NAME = os.environ.get("AGENT_NAME", DEFAULT_AGENT_NAME)
REGION = os.environ.get("REGION", "unknown-region")
PROJECT_ID = os.environ.get("PROJECT_ID", "unknown-project")

# Force ADK to use pure API keys instead of Vertex AI workload identity
if "GEMINI_VERTEXAI" in os.environ:
    del os.environ["GEMINI_VERTEXAI"]

@app.get("/")
def health_check() -> Dict[str, str]:
    import socket
    return {
        "message": "Welcome to the Enterprise Multi-Agent Banking Mesh Orchestrator API (v2.1.0)!",
        "status": HEALTH_STATUS_OK, 
        "agent": AGENT_NAME,
        "region": REGION,
        "pod_id": socket.gethostname()
    }

@app.get("/stress_test")
def stress_test(duration: int = 15):
    import time
    import math
    end_time = time.time() + duration
    while time.time() < end_time:
        math.factorial(10000)
    return {"status": "stress test completed", "message": f"CPU spiked for {duration} seconds"}

@app.get("/user-data/{user_id}")
def get_user_data(user_id: str):
    """Fetch profile from Profiler pod which securely reads from GCS"""
    import requests
    try:
        resp = requests.get(f"{PROFILER_URL}/profile/{user_id}", timeout=5)
        resp.raise_for_status()
        return resp.json().get("raw_data", {})
    except Exception as e:
        return {"error": f"Failed to fetch cloud profile for {user_id}: {e}"}

# Define the ADK Agent for Intent Routing (v2.1.0)
orchestrator_agent = Agent(
    name="orchestrator_agent",
    model="gemini-2.5-flash",
    instruction="""
    Determine the intent of the following user message. 
    Is the user asking for 'Wealth Advice' (investments, stocks) or 'Expense Analysis' (budgeting, transactions, debt)?
    Reply with exactly one word: WEALTH or EXPENSE.
    """
)

# Define the ADK Agent for Conversation Memory Summarization (Phase 6)
summarizer_agent = Agent(
    name="summarizer_agent",
    model="gemini-2.5-flash",
    instruction="""
    Summarize the recent interaction between the user and the system in 1-2 sentences. 
    Keep it extremely concise. Example: "The user asked about Tesla stock options and was routed to the Wealth Advisor."
    """
)

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat", response_model=Dict[str, Any])
async def handle_chat(request: ChatRequest) -> Dict[str, Any]:
    """
    The main API Gateway entrypoint. 
    Intercepts the message, gets the user context from the Profiler,
    detects the intent using ADK, and routes to the downstream pod.
    """
    user_id = request.user_id
    message = request.message

    # 1. Fetch User Context from the Profiler Pod (Memory Engine)
    try:
        profiler_resp = requests.get(f"{PROFILER_URL}/profile/{user_id}")
        profiler_resp.raise_for_status()
        user_summary = profiler_resp.json().get("summary", "")
    except Exception as e:
        print(f"Warning: Could not reach Profiler at {PROFILER_URL}: {e}")
        user_summary = "[MOCK] Default User Context"

    # 2. Intent Routing
    try:
        from google.adk import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
        from google.genai import types

        session_service = InMemorySessionService()
        session_service.create_session_sync(
            app_name="orchestrator_app", 
            session_id=f"session_orchestrator_{user_id}", 
            user_id=user_id
        )

        runner = Runner(
            app_name="orchestrator_app",
            agent=orchestrator_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService(),
        )

        intent = "WEALTH"
        msg = types.Content(role="user", parts=[types.Part.from_text(text=f"User Context: {user_summary}\n\nMessage: {message}")])
        async for event in runner.run_async(
            user_id=user_id,
            session_id=f"session_orchestrator_{user_id}",
            new_message=msg
        ):
            # ADK 2.1 Content parsing
            if getattr(event, "content", None) and event.content.parts:
                intent = event.content.parts[0].text.strip().upper()
    except Exception as e:
        print(f"Orchestrator Routing Error: {e}")
        intent = "WEALTH"

    # 3. Route to Downstream Agent Pod
    if "WEALTH" in intent:
        final_answer = f"[Simulated Wealth Advisor Response based on ADK Route: {user_summary}]"
        routed_agent = "Wealth Advisor"
    else:
        final_answer = f"[Simulated Expense Analyst Response based on ADK Route: {user_summary}]"
        routed_agent = "Expense Analyst"

    # 4. Generate Conversation Summary for Memory Engine
    memory_summary = ""
    try:
        from google.adk import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.genai import types

        mem_session_service = InMemorySessionService()
        mem_session_service.create_session_sync(
            app_name="summarizer_app", 
            session_id=f"session_mem_{user_id}", 
            user_id=user_id
        )

        mem_runner = Runner(
            app_name="summarizer_app",
            agent=summarizer_agent,
            session_service=mem_session_service
        )

        mem_prompt = f"User Message: {message}\nSystem Action: Routed to {routed_agent}\nSystem Response: {final_answer}"
        msg = types.Content(role="user", parts=[types.Part.from_text(text=mem_prompt)])
        
        async for event in mem_runner.run_async(
            user_id=user_id,
            session_id=f"session_mem_{user_id}",
            new_message=msg
        ):
            if getattr(event, "content", None) and event.content.parts:
                memory_summary += event.content.parts[0].text
                
    except Exception as e:
        print(f"Memory Summarization Error: {e}")
        memory_summary = "Failed to summarize conversation."

    return {
        "status": "success",
        "routed_to": routed_agent,
        "user_context_used": user_summary,
        "final_answer": final_answer,
        "new_memory_summary": memory_summary.strip()
    }

# Serve the frontend UI directory directly from the cloud Orchestrator as a fallback route
if os.path.isdir("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
