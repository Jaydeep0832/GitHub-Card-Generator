import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent import github_card_agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai.types import Content, Part
import uvicorn

app = FastAPI(title="GitHub Dev Card Generator")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# Runner
runner = Runner(
    app_name="github_card_app",
    agent=github_card_agent,
    session_service=session_service,
    memory_service=memory_service,
    auto_create_session=True
)

# Request Model
class GenerateRequest(BaseModel):
    username: str

# Ensure static directory exists
CARDS_DIR = os.path.join(os.path.dirname(__file__), "static", "cards")
os.makedirs(CARDS_DIR, exist_ok=True)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/generate")
async def generate_card(request: GenerateRequest):
    username = request.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    user_id = "default_user"
    session_id = f"session_{username}"

    # Ensure session exists
    try:
        await session_service.get_session(
            app_name="github_card_app",
            user_id=user_id,
            session_id=session_id
        )
    except Exception:
        await session_service.create_session(
            app_name="github_card_app",
            user_id=user_id,
            session_id=session_id
        )

    message = Content(
        role="user",
        parts=[Part(text=f"Generate a dev card for {username}")]
    )

    card_url = None
    
    # Run the agent (regular generator)
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            # We look for the final response which contains the path
            if hasattr(event, 'text') and event.text:
                # The agent usually mentions the path in its final text
                if "/static/cards/" in event.text:
                    # Extract path from text if possible, or we can trust the tool was called
                    card_url = f"/static/cards/{username}.html"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    if not card_url:
        # Fallback check if file exists
        file_path = os.path.join(CARDS_DIR, f"{username}.html")
        if os.path.exists(file_path):
            card_url = f"/static/cards/{username}.html"
        else:
            raise HTTPException(status_code=500, detail="Failed to generate card")

    return {
        "username": username,
        "card_url": card_url
    }

@app.get("/card/{username}")
async def get_card(username: str):
    file_path = os.path.join(CARDS_DIR, f"{username}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Card not found")

# Serve static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
