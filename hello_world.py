import asyncio
import os

# Set the new Gemini API key
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "INSERT_KEY_HERE_FOR_LOCAL_TESTING")

from google.genai import types
from google.adk import Agent
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.runners import Runner

async def main():
    print("Initializing pristine ADK 2.1 Hello World Agent...")
    
    # 1. Define the Agent
    hello_agent = Agent(
        name="hello_agent",
        model="gemini-2.5-flash",
        instruction="You are a friendly assistant. Keep your answers brief and start with 'Hello World!'"
    )

    # 2. Setup Session Management (Required in ADK 2.1)
    session_service = InMemorySessionService()
    session_service.create_session_sync(
        app_name="hello_app", 
        session_id="session_1", 
        user_id="developer"
    )

    # 3. Create the Runner
    runner = Runner(
        app_name="hello_app",
        agent=hello_agent,
        session_service=session_service
    )

    print("\nSending prompt 'Hello World' to Gemini 2.5 Flash...")
    print("--------------------------------------------------")
    
    # 4. Run the inference
    try:
        response_stream = runner.run_async(
            user_id="developer",
            session_id="session_1", 
            new_message=types.Content(
                role="user", 
                parts=[types.Part.from_text(text="Hello World")]
            )
        )
        
        async for event in response_stream:
            # ADK 2.1 event structure uses genai.types.Content
            if getattr(event, "content", None) and event.content.parts:
                print(event.content.parts[0].text, end="", flush=True)
                
    except Exception as e:
        print(f"\nError connecting to Gemini: {e}")
    
    print("\n\n--------------------------------------------------")

if __name__ == "__main__":
    # Ensure asyncio event loop runs properly on Windows
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
