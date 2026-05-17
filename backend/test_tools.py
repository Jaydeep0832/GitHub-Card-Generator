import asyncio
import os
import json
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card
from dotenv import load_dotenv

async def main():
    load_dotenv()
    username = "torvalds"
    
    print(f"--- 1. Scraping GitHub for {username} ---")
    try:
        github_data = await scrape_github(username)
        print("Scrape successful.")
    except Exception as e:
        print(f"FAILED scrape_github: {e}")
        return

    print(f"--- 2. Analyzing profile ---")
    try:
        analysis = await analyze_profile(github_data)
        print("Analysis successful.")
        print(f"Vibe: {analysis.get('developer_vibe')}")
        print(f"Theme: {analysis.get('card_theme')}")
    except Exception as e:
        print(f"FAILED analyze_profile: {e}")
        print("Note: This likely failed because GOOGLE_API_KEY is not set correctly in .env")
        return

    print(f"--- 3. Generating HTML card ---")
    try:
        html = await generate_card_html(username, github_data, analysis)
        print("HTML generation successful.")
    except Exception as e:
        print(f"FAILED generate_card_html: {e}")
        return

    print(f"--- 4. Saving card ---")
    try:
        path = await save_card(username, html)
        print(f"Card saved to: {path}")
    except Exception as e:
        print(f"FAILED save_card: {e}")
        return

    print("--- End to End Test Completed ---")

if __name__ == "__main__":
    asyncio.run(main())
