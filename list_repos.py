import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("GITHUB_TOKEN")

if not token:
    print("Error: GITHUB_TOKEN not found in .env")
    exit(1)

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

with httpx.Client() as client:
    response = client.get("https://api.github.com/user/repos", headers=headers)
    if response.status_code == 200:
        repos = [r['name'] for r in response.json()]
        print(f"Repositories: {repos}")
    else:
        print(f"Failed to list repositories: {response.status_code}")
        print(response.text)
