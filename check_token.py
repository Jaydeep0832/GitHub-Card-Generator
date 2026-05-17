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
    response = client.get("https://api.github.com/user", headers=headers)
    if response.status_code == 200:
        print(f"Token is valid for user: {response.json()['login']}")
    else:
        print(f"Token validation failed: {response.status_code}")
        print(response.text)
