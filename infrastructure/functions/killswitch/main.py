import base64
import json
import os
import requests
from google.cloud import secretmanager

def get_github_token(project_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/github-pat/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def killswitch(event, context):
    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        data = json.loads(pubsub_message)
        
        cost_amount = data.get('costAmount', 0)
        budget_amount = data.get('budgetAmount', 9)
        
        print(f"Received billing alert. Cost: {cost_amount}, Budget: {budget_amount}")
        
        if cost_amount >= budget_amount:
            print("BUDGET EXCEEDED! Initiating automated killswitch.")
            project_id = os.environ.get('GCP_PROJECT')
            github_repo = os.environ.get('GITHUB_REPO', 'Eran-Meir/multi-agent-banking-mesh')
            
            token = get_github_token(project_id)
            
            url = f"https://api.github.com/repos/{github_repo}/actions/workflows/6-destroy-all-and-verify.yml/dispatches"
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            payload = {"ref": "main"}
            
            response = requests.post(url, headers=headers, json=payload)
            print(f"GitHub Action trigger response: {response.status_code}")
            response.raise_for_status()
        else:
            print("Budget not exceeded yet. No action taken.")
    except Exception as e:
        print(f"Error processing killswitch event: {e}")
