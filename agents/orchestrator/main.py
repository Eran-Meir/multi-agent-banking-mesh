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

from google.cloud import storage
import json

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
ENVIRONMENT = os.environ.get("ENVIRONMENT", "test")
BUCKET_NAME = f"{ENVIRONMENT}-banking-mesh-data-{PROJECT_ID}"

# Initialize Storage Client
try:
    storage_client = storage.Client()
except Exception as e:
    storage_client = None
    print(f"Warning: Could not initialize storage client: {e}")

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
        resp = requests.get(f"{PROFILER_URL}/profile/{user_id}", timeout=30)
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

# Downstream Agent: Wealth Advisor
wealth_advisor_agent = Agent(
    name="wealth_advisor_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a professional Wealth Advisor. You must answer the user's question based strictly on their AI Profile summary provided below.
    If they have high debt and low savings, discourage risky investments.
    Be concise, helpful, and highly personalized.
    """
)

# Downstream Agent: Expense Analyst
expense_analyst_agent = Agent(
    name="expense_analyst_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a strict Expense Analyst. Analyze the user's question based strictly on their AI Profile summary provided below.
    Focus on budgeting, debt reduction, and transaction management.
    Be concise, practical, and highly personalized.
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

# Define the ADK Agent for the Bank Analyst (Executive Dashboard)
bank_analyst_agent = Agent(
    name="bank_analyst_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are the Executive Bank Analyst AI. You are providing insights to the bank's executives.
    Analyze the provided global_trends.json data, which contains the recent chat summaries across all users.
    Answer the executive's question based strictly on this trend data.
    Be professional, concise, and highlight the most requested features or common issues.
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
    final_answer = ""
    routed_agent = ""
    try:
        from google.adk import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.genai import types
        
        downstream_session_service = InMemorySessionService()
        downstream_session_service.create_session_sync(
            app_name="downstream_app", 
            session_id=f"session_downstream_{user_id}", 
            user_id=user_id
        )

        if "WEALTH" in intent:
            target_agent = wealth_advisor_agent
            routed_agent = "Wealth Advisor"
        else:
            target_agent = expense_analyst_agent
            routed_agent = "Expense Analyst"
            
        downstream_runner = Runner(
            app_name="downstream_app",
            agent=target_agent,
            session_service=downstream_session_service
        )
        
        downstream_prompt = f"User Profile Context:\n{user_summary}\n\nUser Message:\n{message}"
        downstream_msg = types.Content(role="user", parts=[types.Part.from_text(text=downstream_prompt)])
        
        async for event in downstream_runner.run_async(
            user_id=user_id,
            session_id=f"session_downstream_{user_id}",
            new_message=downstream_msg
        ):
            if getattr(event, "content", None) and event.content.parts:
                final_answer += event.content.parts[0].text
                
    except Exception as e:
        print(f"Downstream Agent Error: {e}")
        final_answer = f"[Error executing {routed_agent} via Gemini: {e}]"

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

    # 5. Append to Global Trends
    if storage_client and memory_summary and "Failed" not in memory_summary:
        try:
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob("global_trends.json")
            if blob.exists():
                trends_data = json.loads(blob.download_as_string())
            else:
                trends_data = {"recent_sessions": []}
            
            trends_data["recent_sessions"].append({
                "user_id": user_id,
                "timestamp": __import__('time').time(),
                "summary": memory_summary.strip()
            })
            
            # Keep only last 100 to save space
            trends_data["recent_sessions"] = trends_data["recent_sessions"][-100:]
            blob.upload_from_string(json.dumps(trends_data, indent=2), content_type='application/json')
        except Exception as e:
            print(f"Warning: Failed to update global trends in GCS: {e}")

        # 6. Append to User's Personal Memory
        try:
            user_blob = bucket.blob(f"{user_id}.json")
            if user_blob.exists():
                user_data = json.loads(user_blob.download_as_string())
                if "past_interactions" not in user_data:
                    user_data["past_interactions"] = []
                user_data["past_interactions"].append({
                    "timestamp": __import__('time').time(),
                    "summary": memory_summary.strip()
                })
                # Keep last 20
                user_data["past_interactions"] = user_data["past_interactions"][-20:]
                user_blob.upload_from_string(json.dumps(user_data, indent=2), content_type='application/json')
        except Exception as e:
            print(f"Warning: Failed to update user past interactions in GCS: {e}")

    return {
        "status": "success",
        "routed_to": routed_agent,
        "user_context_used": user_summary,
        "final_answer": final_answer,
        "new_memory_summary": memory_summary.strip()
    }

class AnalystRequest(BaseModel):
    message: str

@app.post("/analyst/chat", response_model=Dict[str, Any])
async def handle_analyst_chat(request: AnalystRequest) -> Dict[str, Any]:
    message = request.message
    
    # Read global trends from GCS
    trends_json_str = "{}"
    if storage_client:
        try:
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob("global_trends.json")
            if blob.exists():
                trends_json_str = blob.download_as_string().decode('utf-8')
            else:
                trends_json_str = '{"message": "No trends recorded yet."}'
        except Exception as e:
            trends_json_str = f'{{"error": "Failed to read trends: {e}"}}'
            
    final_answer = ""
    try:
        from google.adk import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.genai import types
        
        analyst_session_service = InMemorySessionService()
        analyst_session_service.create_session_sync(
            app_name="analyst_app", 
            session_id="session_analyst_executive", 
            user_id="executive"
        )
        
        analyst_runner = Runner(
            app_name="analyst_app",
            agent=bank_analyst_agent,
            session_service=analyst_session_service
        )
        
        analyst_prompt = f"Global Trends Data:\n{trends_json_str}\n\nExecutive Question:\n{message}"
        analyst_msg = types.Content(role="user", parts=[types.Part.from_text(text=analyst_prompt)])
        
        async for event in analyst_runner.run_async(
            user_id="executive",
            session_id="session_analyst_executive",
            new_message=analyst_msg
        ):
            if getattr(event, "content", None) and event.content.parts:
                final_answer += event.content.parts[0].text
    except Exception as e:
        print(f"Analyst Agent Error: {e}")
        final_answer = f"[Error executing Bank Analyst Agent: {e}]"
        
    return {
        "status": "success",
        "final_answer": final_answer
    }

# Serve the frontend UI directory directly from the cloud Orchestrator as a fallback route
if os.path.isdir("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
