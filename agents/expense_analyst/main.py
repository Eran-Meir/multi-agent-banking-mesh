from fastapi import FastAPI
import os

app = FastAPI()

AGENT_NAME = os.getenv("AGENT_NAME", "Unknown Agent")

@app.get("/")
def health_check():
    return {"status": "healthy", "agent": AGENT_NAME}

@app.post("/process")
def process_event(event: dict):
    return {"status": "processed", "agent": AGENT_NAME, "event": event}
