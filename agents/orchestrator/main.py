import os
import time
import math
from typing import Dict, Any
from fastapi import FastAPI

# --- Configuration Constants ---
DEFAULT_AGENT_NAME = "Orchestrator Agent"
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
    return {
        "message": "Hello World from the Banking Mesh Orchestrator!",
        "status": HEALTH_STATUS_OK, 
        "agent": AGENT_NAME
    }

@app.post("/process", response_model=Dict[str, Any])
def process_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an incoming event payload.
    """
    return {"status": PROCESS_STATUS_OK, "agent": AGENT_NAME, "event": event}

@app.get("/stress_test")
def stress_test(duration: int = 15):
    """Simulates high CPU load for a few seconds to trigger HPA."""
    # Compute factorial of a large number for `duration` seconds to max out CPU
    end_time = time.time() + duration
    while time.time() < end_time:
        math.factorial(10000)
    return {"status": "stress test completed", "message": f"CPU spiked for {duration} seconds"}
