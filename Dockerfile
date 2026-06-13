FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all agents
COPY agents/ agents/

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "agents.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8080"]
