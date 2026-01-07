import json
import os
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def get_daily_props():
    try:
        SPORTSRADAR_KEY = os.environ["SPORTSRADAR_KEY"]
        GROK_API_KEY = os.environ["GROK_API_KEY"]  # If using Grok for reasoning

        today = datetime.utcnow().strftime('%Y-%m-%d')
        base_url = f"https://api.sportradar.us/nhl/trial/v8/en"

        # API pulls (official stats)
        schedule_url = f"{base_url}/games/{today}/schedule.json?api_key={SPORTSRADAR_KEY}"
        games_resp = requests.get(schedule_url)
        games_resp.raise_for_status()
        games_data = games_resp.json().get("games", [])
        games_summary = json.dumps([{"home": g["home"]["name"], "away": g["away"]["name"], "id": g["id"]} for g in games_data])

        # Example player stats pull (expand as needed – e.g., loop game IDs for boxscores/player logs)
        # stats_example = requests.get(f"{base_url}/seasons/2025/REG/statistics.json?api_key={SPORTSRADAR_KEY}").json()

        # Scrape supplements
        def extract_tables(url):
            try:
                tables = pd.read_html(url)
                return "\n\n".join([df.to_string(index=False) for df in tables[:5]])
            except:
                return "No tables."

        def extract_text(url):
            try:
                html = requests.get(url).text
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text(separator='\n', strip=True)[:10000]
            except:
                return "Error."

        matchup_text = extract_text("https://www.dailyfantasyfuel.com/nhl/matchup-analysis/")
        lineups_text = extract_text("https://www.dailyfantasyfuel.com/nhl/starting-lineups/")
        ga_text = extract_tables("https://shotpropz.com/nhl/goals-against-by-position/")
        sog_text = extract_tables("https://shotpropz.com/nhl/sog-against-by-position/")

        # Cumulative prompt (adapt for Grok or direct logic)
        cumulative_prompt = f"""
Data-driven anytime goal scorer and SOG projections only from provided data.

Today's games/schedule: {games_summary} {matchup_text}
Lineups/goalies: {lineups_text}
Goals against position: {ga_text}
SOG against position: {sog_text}

Output JSON: {{"sog_props": [{{player, team, opponent, projected_sog, confidence, reasoning}}], "atg_props": [similar for prob]}}
Top 10-15, sorted by confidence (0-100).
"""

        # Add Grok call if key set, or simple logic here
        # For now, placeholder return (expand with API player logs for real projections)
        return {"sog_props": [], "atg_props": []}  # Fill with logic/API parsing

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
