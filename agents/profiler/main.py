import os
import json
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from google.adk import Agent

from google.cloud import storage

# --- Configuration Constants ---
DEFAULT_AGENT_NAME = "Profiler Agent"
HEALTH_STATUS_OK = "healthy"
PROJECT_ID = os.environ.get("PROJECT_ID", "unknown-project")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "test")
BUCKET_NAME = f"{ENVIRONMENT}-banking-mesh-data-{PROJECT_ID}"

app = FastAPI(title=DEFAULT_AGENT_NAME)
AGENT_NAME = os.environ.get("AGENT_NAME", DEFAULT_AGENT_NAME)
REGION = os.environ.get("REGION", "unknown-region")

# Force ADK to use pure API keys instead of Vertex AI workload identity
if "GEMINI_VERTEXAI" in os.environ:
    del os.environ["GEMINI_VERTEXAI"]

# Initialize Storage Client
try:
    storage_client = storage.Client()
except Exception as e:
    storage_client = None
    print(f"Warning: Could not initialize storage client: {e}")

# --- Define Profiler Agent ---
profiler_agent = Agent(
    name="profiler_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a highly analytical core banking Profiler Agent.
    Analyze the provided raw transaction, demographic data, and especially the past_interactions array.
    Provide a concise, 2-sentence psychological and financial summary of this user's behavior.
    If the user has recent past_interactions, prominently mention their active goals or repeated questions.
    Do not repeat the numbers. Deduce their financial personality, risk tolerance, and any red flags.
    """
)

@app.get("/")
def health_check() -> Dict[str, str]:
    return {"status": HEALTH_STATUS_OK, "agent": AGENT_NAME, "region": REGION}

@app.get("/profile/{user_id}", response_model=Dict[str, Any])
async def get_or_generate_profile(user_id: str) -> Dict[str, Any]:
    """
    Memory Engine Endpoint using ADK.
    Reads JSON data from GCS, runs Agentic Inference, caches the deduction, and returns.
    """
    if not storage_client:
        raise HTTPException(status_code=500, detail="Storage client not initialized")

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"{user_id}.json")
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail=f"User {user_id} not found in bucket {BUCKET_NAME}.")
            
        data_str = blob.download_as_string()
        user_data = json.loads(data_str)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error accessing GCS: {str(e)}")

    import time
    
    # Fast-Path User Cache
    cached_summary = user_data.get("latest_ai_models_access_summary")
    profiler_metadata = user_data.get("profiler_metadata", {
        "last_evaluated_timestamp": 0,
        "actions_since_evaluation": 0
    })
    
    current_time = time.time()
    last_eval = profiler_metadata.get("last_evaluated_timestamp", 0)
    actions_count = profiler_metadata.get("actions_since_evaluation", 0)
    
    # Increment action count (e.g. this chat message)
    actions_count += 1
    profiler_metadata["actions_since_evaluation"] = actions_count
    user_data["profiler_metadata"] = profiler_metadata
    
    # Re-evaluate if > 30 days or actions >= 5
    thirty_days = 30 * 24 * 60 * 60
    needs_reevaluation = (actions_count >= 5) or ((current_time - last_eval) > thirty_days) or not cached_summary
    
    if cached_summary and not needs_reevaluation:
        # Upload incremented action count but return cache
        try:
            blob.upload_from_string(json.dumps(user_data, indent=2), content_type='application/json')
        except Exception:
            pass
        return {"user_id": user_id, "summary": cached_summary, "cached": True, "raw_data": user_data}

    # Slow-Path Inference
    prompt = f"DATA:\n{json.dumps(user_data, indent=2)}"
    try:
        from google.adk import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
        from google.genai import types
        
        session_service = InMemorySessionService()
        session_service.create_session_sync(
            app_name="profiler_app", 
            session_id=f"session_profiler_{user_id}", 
            user_id=user_id
        )
        
        runner = Runner(
            app_name="profiler_app",
            agent=profiler_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService(),
        )
        
        inferred_summary = ""
        msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        async for event in runner.run_async(
            user_id=user_id,
            session_id=f"session_profiler_{user_id}",
            new_message=msg
        ):
            # ADK 2.1 Content parsing
            if getattr(event, "content", None) and event.content.parts:
                inferred_summary = event.content.parts[0].text
    except Exception as e:
        inferred_summary = f"[ADK MOCK INFERENCE] Could not reach Gemini: {e}"

    # Cache back to GCS Database
    user_data["latest_ai_models_access_summary"] = inferred_summary
    user_data["profiler_metadata"]["actions_since_evaluation"] = 0
    user_data["profiler_metadata"]["last_evaluated_timestamp"] = time.time()
    try:
        blob.upload_from_string(json.dumps(user_data, indent=2), content_type='application/json')
    except Exception as e:
        print(f"Warning: Failed to save cache back to GCS: {e}")

    return {"user_id": user_id, "summary": inferred_summary, "cached": False, "raw_data": user_data}

