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

# Force ADK to use Vertex AI instead of Google AI Studio
os.environ["GEMINI_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = REGION

# Initialize Storage Client
try:
    storage_client = storage.Client()
except Exception as e:
    storage_client = None
    print(f"Warning: Could not initialize storage client: {e}")

from google.adk.models import google_llm
from google.genai import Client
from functools import cached_property

class VertexGemini(google_llm.Gemini):
    @cached_property
    def api_client(self) -> Client:
        return Client(vertexai=True, project=PROJECT_ID, location=REGION)

# --- Define Profiler Agent ---
profiler_agent = Agent(
    name="profiler_agent",
    model=VertexGemini(model="gemini-2.5-flash"),
    instruction="""
    You are a highly analytical core banking Profiler Agent.
    Analyze the provided raw transaction and demographic data for a user.
    Provide a concise, 2-sentence psychological and financial summary of this user's behavior.
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

    # Fast-Path User Cache
    cached_summary = user_data.get("latest_ai_models_access_summary")
    if cached_summary:
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
            session_id=f"session_{user_id}", 
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
            session_id=f"session_{user_id}",
            new_message=msg
        ):
            if event.is_final_response():
                inferred_summary = event.content
    except Exception as e:
        inferred_summary = f"[ADK MOCK INFERENCE] Could not reach Gemini: {e}"

    # Cache back to GCS Database
    user_data["latest_ai_models_access_summary"] = inferred_summary
    try:
        blob.upload_from_string(json.dumps(user_data, indent=2), content_type='application/json')
    except Exception as e:
        print(f"Warning: Failed to save cache back to GCS: {e}")

    return {"user_id": user_id, "summary": inferred_summary, "cached": False, "raw_data": user_data}

