import json
import os
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def get_daily_props():
    SPORTSRADAR_KEY = os.environ.get("SPORTSRADAR_KEY", "")
    GROK_API_KEY = os.environ.get("GROK_API_KEY", "")

    games_summary = "No schedule data available (trial or no games)"

    if SPORTSRADAR_KEY:
        try:
            today = datetime.utcnow()
            year = today.strftime('%Y')
            month = today.strftime('%m').zfill(2)
            day = today.strftime('%d').zfill(2)
            base_url = "https://api.sportradar.us/nhl/trial/v8/en"
            schedule_url = f"{base_url}/games/{year}/{month}/{day}/schedule.json?api_key={SPORTSRADAR_KEY}"
            schedule_resp = requests.get(schedule_url, timeout=10)
            if schedule_resp.status_code == 200:
                schedule_data = schedule_resp.json().get("games", [])
                games_summary = json.dumps([{"home": g.get("home", {}).get("name"), "away": g.get("away", {}).get("name"), "id": g.get("id")} for g in schedule_data])
        except:
            pass  # Fallback to scraped

    # Scrape always (core for model)
    def extract_tables(url):
        try:
            tables = pd.read_html(url, timeout=10)
            return "\n\n".join([df.to_string(index=False) for df in tables[:10]])
        except:
            return "No tables."

    def extract_text(url):
        try:
            html = requests.get(url, timeout=10).text
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text(separator='\n', strip=True)[:15000]
        except:
            return "Error."

    matchup_text = extract_text("https://www.dailyfantasyfuel.com/nhl/matchup-analysis/")
    lineups_text = extract_text("https://www.dailyfantasyfuel.com/nhl/starting-lineups/")
    ga_text = extract_tables("https://shotpropz.com/nhl/goals-against-by-position/")
    sog_text = extract_tables("https://shotpropz.com/nhl/sog-against-by-position/")

    cumulative_prompt = f"""
Data-driven anytime goal scorer and SOG projections from provided data only.

Today's schedule: {games_summary}
Matchups/lineups: {matchup_text} {lineups_text}
Goals against position: {ga_text}
SOG against position: {sog_text}

Output ONLY valid JSON:
{{
  "sog_props": [ {{"player": "", "team": "", "opponent": "", "projected_sog": 0.0, "confidence": 0, "reasoning": ""}} ],
  "atg_props": [ {{"player": "", "team": "", "opponent": "", "projected_prob": 0, "confidence": 0, "reasoning": ""}} ]
}}
Top 10-15 each, sorted by confidence descending (0-100). Use scraped data for strong picks if schedule empty.
"""

    try:
        if GROK_API_KEY:
            grok_resp = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={
                    "model": "grok-4",
                    "messages": [{"role": "user", "content": cumulative_prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.5
                },
                timeout=30
            )
            grok_resp.raise_for_status()
            result = grok_resp.json()["choices"][0]["message"]["content"]
            props_json = json.loads(result)
        else:
            props_json = {"sog_props": [], "atg_props": []}
    except:
        props_json = {"sog_props": [], "atg_props": [], "note": "Model fallback – check keys"}

    return props_json
