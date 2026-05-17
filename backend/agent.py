import os
import sys
from google.adk import Agent, Runner
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioServerParameters, StdioConnectionParams
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from dotenv import load_dotenv

load_dotenv()

# Path to the MCP server script
mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")

# Create the MCP Toolset using stdio transport
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[mcp_server_path]
        ),
        timeout=60.0
    )
)

# Define the ADK agent
github_card_agent = Agent(
    name="github_card_agent",
    instruction=(
        "You are a GitHub profile dev card generator. When a user gives you a GitHub username, "
        "you MUST call the create_github_card tool with that username. "
        "Return the resulting URL to the user."
    ),
    model="gemini-flash-lite-latest",
    tools=[mcp_toolset]
)

# Shared session service
session_service = InMemorySessionService()

def get_runner():
    """Returns a runner instance for the agent."""
    return Runner(
        app_name="github_card_app",
        agent=github_card_agent,
        session_service=session_service
    )

if __name__ == "__main__":
    # Simple CLI test for the agent
    async def run_test():
        # Manually create a session before running
        await session_service.create_session(
            app_name="github_card_app",
            user_id="test_user",
            session_id="test_session"
        )
        
        runner = get_runner()
        # Create a Content object for the new message
        message = Content(
            role="user",
            parts=[Part(text="Generate a developer card for GitHub user: torvalds")]
        )
        
        # Runner.run is a regular generator
        for event in runner.run(
            user_id="test_user",
            session_id="test_session",
            new_message=message
        ):
            # Print text content if available in the event
            if hasattr(event, 'content') and event.content:
                print(event.content)
            elif hasattr(event, 'text') and event.text:
                print(event.text)
            else:
                # Fallback to printing the event itself for debugging
                pass

    import asyncio
    asyncio.run(run_test())
