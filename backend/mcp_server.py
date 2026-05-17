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
model = genai.GenerativeModel("gemini-flash-lite-latest")

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
    """Generate a self-contained HTML developer card with a modern glassmorphism UI."""
    
    repos_html = "".join([
        f'''
        <div class="group flex justify-between items-center p-3 mb-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 hover:border-indigo-400/50 transition-all duration-300">
            <div class="flex flex-col">
                <span class="font-semibold text-gray-100 group-hover:text-indigo-300 transition-colors">{r["name"]}</span>
                <span class="text-xs text-gray-400">{r["language"] or 'N/A'}</span>
            </div>
            <div class="flex items-center gap-1 text-yellow-400/90 text-sm font-medium bg-yellow-400/10 px-2 py-1 rounded-md">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                {r["stars"]}
            </div>
        </div>
        '''
        for r in github_data["top_repos"][:3]
    ])

    skills_html = "".join([
        f'<span class="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold shadow-[0_0_10px_rgba(99,102,241,0.1)]">{skill}</span>'
        for skill in analysis.get("top_skills", [])
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{github_data['name']} - GitHub Dev Card</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: transparent; /* Transparent so it blends in iframe */
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .glass-card {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 27, 75, 0.8) 100%);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            box-shadow: 0 0 40px rgba(99, 102, 241, 0.15), inset 0 0 20px rgba(255, 255, 255, 0.05);
            position: relative;
            overflow: hidden;
        }}
        .glass-card::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}
        .card-content {{
            position: relative;
            z-index: 1;
        }}
        .avatar-glow {{
            box-shadow: 0 0 25px rgba(99, 102, 241, 0.5);
        }}
    </style>
</head>
<body>
    <div class="glass-card w-full max-w-md rounded-2xl p-8 text-white">
        <div class="card-content flex flex-col items-center text-center">
            
            <!-- Avatar & Header -->
            <div class="relative mb-4">
                <div class="absolute inset-0 bg-indigo-500 rounded-full blur-md opacity-50"></div>
                <img src="{github_data['avatar_url']}" alt="Avatar" class="relative w-28 h-28 rounded-full border-2 border-indigo-400 avatar-glow object-cover">
            </div>
            
            <h1 class="text-3xl font-bold tracking-tight mb-1 bg-gradient-to-r from-white to-indigo-200 bg-clip-text text-transparent">{github_data['name']}</h1>
            <a href="https://github.com/{username}" target="_blank" class="text-indigo-400 font-medium hover:text-indigo-300 transition-colors mb-3">@{username}</a>
            
            <!-- Vibe -->
            <p class="text-gray-300 italic text-sm mb-6 leading-relaxed px-4">"{analysis.get('developer_vibe')}"</p>
            
            <!-- Skills -->
            <div class="flex flex-wrap justify-center gap-2 mb-6">
                {skills_html}
            </div>
            
            <!-- Stats -->
            <div class="flex w-full justify-around py-4 border-y border-white/10 mb-6 bg-white/5 rounded-xl">
                <div class="flex flex-col items-center">
                    <span class="text-2xl font-bold text-white">{github_data['public_repos']}</span>
                    <span class="text-xs text-indigo-300 uppercase tracking-wider font-semibold mt-1">Repositories</span>
                </div>
                <div class="w-px bg-white/10"></div>
                <div class="flex flex-col items-center">
                    <span class="text-2xl font-bold text-white">{github_data['followers']}</span>
                    <span class="text-xs text-indigo-300 uppercase tracking-wider font-semibold mt-1">Followers</span>
                </div>
            </div>
            
            <!-- Top Projects -->
            <div class="w-full text-left">
                <h3 class="text-xs text-indigo-300 uppercase tracking-wider font-bold mb-3 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                    </svg>
                    Top Projects
                </h3>
                <div class="flex flex-col">
                    {repos_html}
                </div>
            </div>
            
            <!-- Fun Fact -->
            <div class="mt-6 pt-4 border-t border-white/10 w-full">
                <p class="text-xs text-gray-400 italic">
                    <span class="text-indigo-400 font-semibold not-italic">Fun Fact:</span> {analysis.get('fun_fact')}
                </p>
            </div>

        </div>
    </div>
</body>
</html>"""
    return html

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
