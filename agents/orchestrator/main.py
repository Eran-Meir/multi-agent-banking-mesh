import os
import time
import math
import socket
from typing import Dict, Any
from fastapi import FastAPI

# --- Configuration Constants ---
DEFAULT_AGENT_NAME = "Orchestrator Agent"
HEALTH_STATUS_OK = "healthy"
PROCESS_STATUS_OK = "processed"

# --- Stress Test Constants ---
DEFAULT_STRESS_DURATION_SEC = 15
STRESS_COMPUTATION_LOAD = 10000

# Initialize FastAPI application
app = FastAPI(title=DEFAULT_AGENT_NAME)

AGENT_NAME = os.environ.get("AGENT_NAME", DEFAULT_AGENT_NAME)
REGION = os.environ.get("REGION", "unknown-region")

@app.get("/", response_model=Dict[str, str])
def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the agent is running.
    """
    return {
        "message": "Welcome to the Enterprise Multi-Agent Banking Mesh Orchestrator API!",
        "status": HEALTH_STATUS_OK, 
        "agent": AGENT_NAME,
        "region": REGION,
        "pod_id": socket.gethostname()
    }

@app.post("/process", response_model=Dict[str, Any])
def process_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an incoming event payload.
    """
    return {"status": PROCESS_STATUS_OK, "agent": AGENT_NAME, "event": event}

@app.get("/stress_test")
def stress_test(duration: int = DEFAULT_STRESS_DURATION_SEC):
    """Simulates high CPU load for a few seconds to trigger HPA."""
    # Compute factorial of a large number for `duration` seconds to max out CPU
    end_time = time.time() + duration
    while time.time() < end_time:
        math.factorial(STRESS_COMPUTATION_LOAD)
    return {"status": "stress test completed", "message": f"CPU spiked for {duration} seconds"}
