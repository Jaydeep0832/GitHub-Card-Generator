import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("GITHUB_TOKEN")
repo_name = "GitHub-Card-Generator"

if not token:
    print("Error: GITHUB_TOKEN not found in .env")
    exit(1)

# Try Bearer instead of token
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

data = {
    "name": repo_name,
    "description": "Generate beautiful developer cards from GitHub profiles using Gemini 2.5 Flash and ADK.",
    "private": False
}

with httpx.Client() as client:
    response = client.post("https://api.github.com/user/repos", headers=headers, json=data)
    if response.status_code == 201:
        print(f"Successfully created repository: {response.json()['html_url']}")
    elif response.status_code == 422:
        print("Repository already exists or name is invalid.")
    else:
        print(f"Failed to create repository: {response.status_code}")
        print(response.text)
