import os
import json
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from google.adk import Agent

# --- Configuration Constants ---
DEFAULT_AGENT_NAME = "Profiler Agent"
HEALTH_STATUS_OK = "healthy"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

app = FastAPI(title=DEFAULT_AGENT_NAME)
AGENT_NAME = os.environ.get("AGENT_NAME", DEFAULT_AGENT_NAME)
REGION = os.environ.get("REGION", "unknown-region")

# Define the ADK Agent (Migrated to v2.1.0)
profiler_agent = Agent(
    name="profiler_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a highly analytical core banking Profiler Agent.
    Analyze the provided raw transaction and demographic data for a user.
    Provide a concise, 2-sentence psychological and financial summary of this user's behavior.
    Do not repeat the numbers. Deduce their financial personality, risk tolerance, and any red flags.
    """
)

def get_user_file_path(user_id: str) -> str:
    return os.path.join(DATA_DIR, f"{user_id}.json")

@app.get("/")
def health_check() -> Dict[str, str]:
    return {"status": HEALTH_STATUS_OK, "agent": AGENT_NAME, "region": REGION}

@app.get("/profile/{user_id}", response_model=Dict[str, Any])
def get_or_generate_profile(user_id: str) -> Dict[str, Any]:
    """
    Memory Engine Endpoint using ADK.
    Reads JSON data, runs Agentic Inference, caches the deduction, and returns.
    """
    file_path = get_user_file_path(user_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")

    with open(file_path, "r") as f:
        user_data = json.load(f)

    # Fast-Path User Cache
    cached_summary = user_data.get("latest_ai_models_access_summary")
    if cached_summary:
        return {"user_id": user_id, "summary": cached_summary, "cached": True, "raw_data": user_data}

    # Slow-Path ADK Inference
    prompt = f"DATA:\n{json.dumps(user_data, indent=2)}"
    try:
        response = profiler_agent.run(prompt)
        inferred_summary = response.text
    except Exception as e:
        # Fallback to allow GCP deployments to test the pods even without keys
        inferred_summary = f"[ADK MOCK INFERENCE] Could not reach Gemini: {e}"

    # Cache back to JSON Database
    user_data["latest_ai_models_access_summary"] = inferred_summary
    with open(file_path, "w") as f:
        json.dump(user_data, f, indent=2)

    return {"user_id": user_id, "summary": inferred_summary, "cached": False, "raw_data": user_data}
