from mcp.server.fastmcp import FastMCP
import httpx
import json
import os
import google.generativeai as genai
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

mcp = FastMCP("GithubCardGenerator")

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch and aggregate GitHub user profile information."""
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    async with httpx.AsyncClient(headers=headers) as client:
        # User info
        user_res = await client.get(f"https://api.github.com/users/{username}")
        user_res.raise_for_status()
        user_data = user_res.json()

        # Repos
        repos_res = await client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=30")
        repos_res.raise_for_status()
        repos = repos_res.json()

    # Aggregate languages
    languages = [repo["language"] for repo in repos if repo["language"]]
    top_languages = [lang for lang, count in Counter(languages).most_common(5)]

    # Top 6 repos by stars
    sorted_repos = sorted(repos, key=lambda r: r["stargazers_count"], reverse=True)[:6]
    top_repos = [{
        "name": r["name"],
        "stars": r["stargazers_count"],
        "language": r["language"],
        "description": r["description"]
    } for r in sorted_repos]

    return {
        "name": user_data.get("name") or username,
        "avatar_url": user_data.get("avatar_url"),
        "bio": user_data.get("bio"),
        "location": user_data.get("location"),
        "public_repos": user_data.get("public_repos"),
        "followers": user_data.get("followers"),
        "top_repos": top_repos,
        "languages": top_languages
    }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Use AI to analyze the GitHub profile and determine a developer vibe."""
    prompt = f"""
    Analyze this GitHub profile data and return a JSON object with:
    - developer_vibe: A 1-sentence personality description.
    - top_skills: A list of 3 skills based on repos and bio.
    - fun_fact: A clever or surprising inference from their work.
    - card_theme: One of ["hacker", "builder", "researcher", "designer", "open-source-hero"].

    Data: {json.dumps(github_data)}
    
    Response MUST be valid JSON.
    """
    
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return json.loads(response.text)

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a self-contained HTML developer card."""
    theme = analysis.get("card_theme", "builder")
    
    theme_styles = {
        "hacker": "bg-gray-900 text-green-400 border-green-500",
        "builder": "bg-white text-gray-800 border-blue-500",
        "researcher": "bg-indigo-50 text-indigo-900 border-indigo-400",
        "designer": "bg-pink-50 text-pink-900 border-pink-400",
        "open-source-hero": "bg-orange-50 text-orange-900 border-orange-400"
    }
    
    style = theme_styles.get(theme, theme_styles["builder"])
    
    repos_html = "".join([
        f'<div class="mb-2"><strong>{r["name"]}</strong> <span class="text-xs">⭐{r["stars"]} - {r["language"]}</span></div>'
        for r in github_data["top_repos"][:3]
    ])

    skills_html = "".join([
        f'<span class="px-2 py-1 rounded-full bg-opacity-20 bg-current text-xs font-bold mr-1">{skill}</span>'
        for skill in analysis.get("top_skills", [])
    ])

    html = f"""
    <div class="max-w-md mx-auto my-8 p-6 rounded-xl border-t-8 shadow-2xl {style} font-sans">
        <div class="flex items-center gap-4 mb-4">
            <img src="{github_data['avatar_url']}" class="w-20 h-20 rounded-full border-2 border-current" alt="Avatar">
            <div>
                <h2 class="text-2xl font-bold">{github_data['name']}</h2>
                <p class="text-sm opacity-80 italic">{analysis.get('developer_vibe')}</p>
            </div>
        </div>
        <div class="mb-4">{skills_html}</div>
        <div class="grid grid-cols-2 gap-4 mb-4 text-center border-y py-2 border-current border-opacity-20">
            <div><div class="font-bold text-xl">{github_data['public_repos']}</div><div class="text-xs uppercase">Repos</div></div>
            <div><div class="font-bold text-xl">{github_data['followers']}</div><div class="text-xs uppercase">Followers</div></div>
        </div>
        <div class="mb-4">
            <h3 class="text-xs uppercase font-bold mb-2 opacity-60">Top Repositories</h3>
            {repos_html}
        </div>
        <div class="text-xs italic opacity-70">
            <strong>Fun Fact:</strong> {analysis.get('fun_fact')}
        </div>
    </div>
    """
    return html

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save the card HTML and return the file path."""
    abs_path = os.path.join(os.path.dirname(__file__), "static", "cards", f"{username}.html")
    
    # Ensure directory exists (redundant but safe)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return f"/static/cards/{username}.html"

@mcp.tool()
async def create_github_card(username: str) -> str:
    """Fetches a GitHub profile, analyzes it, generates an HTML card, and saves it. Returns the URL path."""
    github_data = await scrape_github(username)
    analysis = await analyze_profile(github_data)
    html = await generate_card_html(username, github_data, analysis)
    return await save_card(username, html)

if __name__ == "__main__":
    mcp.run()
