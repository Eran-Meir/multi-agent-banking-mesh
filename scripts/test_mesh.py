import sys
import json
import requests
import time

sys.stdout.reconfigure(encoding='utf-8')

# The LoadBalancer IP we got from the test environment earlier
ORCHESTRATOR_URL = "http://34.165.48.181"

# The 5 personas we defined
USERS = [
    {"id": "USER_1", "desc": "The Indebted Divorcee", "msg": "Should I invest my last $500 in Tesla options?"},
    {"id": "USER_2", "desc": "The Wealthy Retiree", "msg": "What is the best way to handle my massive dividend payouts this month?"},
    {"id": "USER_3", "desc": "The Fresh College Grad", "msg": "I just got my first paycheck! Should I pay off my student loans or buy a car?"},
    {"id": "USER_4", "desc": "The Serial Entrepreneur", "msg": "My new startup just raised $10M. How should I structure my corporate accounts?"},
    {"id": "USER_5", "desc": "The Reckless Spender", "msg": "I am maxed out on 3 credit cards. Can you analyze my recent transactions?"}
]

def main():
    print("==================================================")
    print("🚀 INIT: ADK 2.0 MULTI-AGENT BANKING MESH TESTER")
    print(f"📡 TARGET: {ORCHESTRATOR_URL}")
    print("==================================================\n")

    # 1. Health Check
    try:
        print("[*] Pinging Orchestrator Health Check...")
        health = requests.get(f"{ORCHESTRATOR_URL}/")
        health.raise_for_status()
        print(f"✅ Orchestrator is ALIVE: {health.json().get('message')}\n")
    except Exception as e:
        print(f"❌ Failed to reach Orchestrator. Is the Test Environment deployed? Error: {e}")
        sys.exit(1)

    # 2. Iterate through users
    for user in USERS:
        print(f"--------------------------------------------------")
        print(f"🧑‍💼 SIMULATING: {user['id']} ({user['desc']})")
        print(f"💬 MESSAGE: \"{user['msg']}\"")
        print(f"--------------------------------------------------")
        
        payload = {
            "user_id": user["id"],
            "message": user["msg"]
        }

        try:
            print("⏳ Forwarding to Orchestrator -> Profiler Memory Engine...")
            start_time = time.time()
            response = requests.post(f"{ORCHESTRATOR_URL}/chat", json=payload)
            response.raise_for_status()
            elapsed = time.time() - start_time

            data = response.json()
            
            print(f"\n🧠 PROFILER DEDUCTION (The Memory Engine):")
            print(f"   > {data.get('user_context_used')}\n")
            
            print(f"🔀 ORCHESTRATOR ADK ROUTE:")
            print(f"   > Routed to: {data.get('routed_to')}\n")
            
            print(f"🤖 FINAL AGENT RESPONSE:")
            print(f"   > {data.get('final_answer')}\n")
            
            print(f"⏱️  Time taken: {elapsed:.2f} seconds\n")
            
        except Exception as e:
            print(f"❌ Error communicating with Mesh: {e}")

if __name__ == "__main__":
    main()
