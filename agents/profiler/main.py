import os
from typing import Dict, Any
from fastapi import FastAPI

# --- Configuration Constants ---
DEFAULT_AGENT_NAME = "Profiler Agent"
HEALTH_STATUS_OK = "healthy"
PROCESS_STATUS_OK = "processed"

# Initialize FastAPI application
app = FastAPI(title=DEFAULT_AGENT_NAME)

AGENT_NAME = os.environ.get("AGENT_NAME", DEFAULT_AGENT_NAME)

@app.get("/", response_model=Dict[str, str])
def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the agent is running.
    """
    return {"status": HEALTH_STATUS_OK, "agent": AGENT_NAME}

@app.post("/process", response_model=Dict[str, Any])
def process_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an incoming event payload.
    """
    return {"status": PROCESS_STATUS_OK, "agent": AGENT_NAME, "event": event}
