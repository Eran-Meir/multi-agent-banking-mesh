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

# Serve the frontend UI directory directly from the cloud Orchestrator
import os
if os.path.isdir("frontend"):
    app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

# Serve the data directory statically so the UI can load it directly
if os.path.isdir("data"):
    app.mount("/data", StaticFiles(directory="data"), name="data")

AGENT_NAME = os.environ.get("AGENT_NAME", DEFAULT_AGENT_NAME)
REGION = os.environ.get("REGION", "unknown-region")

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
    """Fetch raw JSON from Profiler pod so UI can read live cloud data"""
    try:
        resp = requests.get(f"{PROFILER_URL}/profile/{user_id}")
        resp.raise_for_status()
        return resp.json().get("raw_data", {})
    except Exception as e:
        return {"error": f"Failed to fetch cloud profile for {user_id}: {e}"}

# Define the ADK Agent for Intent Routing (v2.1.0)
orchestrator_agent = Agent(
    name="orchestrator_router",
    model="gemini-2.5-flash",
    instruction="""
    Determine the intent of the following user message. 
    Is the user asking for 'Wealth Advice' (investments, stocks) or 'Expense Analysis' (budgeting, transactions, debt)?
    Reply with exactly one word: WEALTH or EXPENSE.
    """
)

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat", response_model=Dict[str, Any])
def handle_chat(request: ChatRequest) -> Dict[str, Any]:
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

    # 2. Intent Routing via ADK 2.0
    try:
        response = orchestrator_agent.run(f"Message: {message}")
        intent = response.text.strip().upper()
    except Exception as e:
        # Fallback to allow testing without live API keys
        intent = "WEALTH"

    # 3. Route to Downstream Agent Pod
    if "WEALTH" in intent:
        final_answer = f"[Simulated Wealth Advisor Response based on ADK Route: {user_summary}]"
        routed_agent = "Wealth Advisor"
    else:
        final_answer = f"[Simulated Expense Analyst Response based on ADK Route: {user_summary}]"
        routed_agent = "Expense Analyst"

    return {
        "status": "success",
        "routed_to": routed_agent,
        "user_context_used": user_summary,
        "final_answer": final_answer
    }
