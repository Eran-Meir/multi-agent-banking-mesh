import base64
import json
import os
from typing import Dict, Any

import requests
from google.cloud import secretmanager

# --- Configuration Constants ---
DEFAULT_COST_FALLBACK = 0.0
DEFAULT_BUDGET_LIMIT = 9.0
DEFAULT_CURRENCY = "USD"
DEFAULT_GITHUB_REPO = "Eran-Meir/multi-agent-banking-mesh"

GITHUB_API_VERSION = "2022-11-28"
GITHUB_ACCEPT_HEADER = "application/vnd.github+json"
NUKE_WORKFLOW_FILENAME = "6-destroy-all-and-verify.yml"
TARGET_BRANCH = "main"

def get_github_token(project_id: str) -> str:
    """
    Retrieves the GitHub Personal Access Token from GCP Secret Manager.
    """
    environment = os.environ.get('ENVIRONMENT', '')
    secret_prefix = f"{environment}-" if environment else ""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_prefix}github-pat/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def killswitch(event: Dict[str, Any], context: Any) -> None:
    """
    Cloud Function triggered by Pub/Sub to monitor billing and trigger
    a GitHub Action if the budget threshold is exceeded.
    """
    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        data = json.loads(pubsub_message)
        
        # Read values from Pub/Sub JSON payload
        cost_amount = float(data.get('costAmount', DEFAULT_COST_FALLBACK))
        budget_amount = float(data.get('budgetAmount', DEFAULT_BUDGET_LIMIT))
        currency_code = data.get('currencyCode', DEFAULT_CURRENCY)
        
        print(f"Received billing alert. Cost: {cost_amount} {currency_code}, Budget Limit: {budget_amount} {currency_code}")
        
        if cost_amount >= budget_amount:
            print(f"BUDGET EXCEEDED ({cost_amount} >= {budget_amount} {currency_code})! Initiating automated killswitch.")
            
            project_id = os.environ.get('GCP_PROJECT')
            if not project_id:
                raise ValueError("GCP_PROJECT environment variable is missing.")
                
            github_repo = os.environ.get('GITHUB_REPO', DEFAULT_GITHUB_REPO)
            token = get_github_token(project_id)
            
            url = f"https://api.github.com/repos/{github_repo}/actions/workflows/{NUKE_WORKFLOW_FILENAME}/dispatches"
            headers = {
                "Accept": GITHUB_ACCEPT_HEADER,
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": GITHUB_API_VERSION
            }
            payload = {"ref": TARGET_BRANCH}
            
            response = requests.post(url, headers=headers, json=payload)
            print(f"GitHub Action trigger response: {response.status_code}")
            response.raise_for_status()
        else:
            print("Budget not exceeded yet. No action taken.")
    except Exception as e:
        print(f"Error processing killswitch event: {e}")
