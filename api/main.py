import json
import os
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")  # Changed to root for Vercel compatibility
def get_daily_props():
    try:
        BALLDONTLIE_KEY = os.environ["BALLDONTLIE_KEY"]
        GROK_API_KEY = os.environ["GROK_API_KEY"]

        today = datetime.utcnow().strftime('%Y-%m-%d')

        headers = {"Authorization": BALLDONTLIE_KEY}
        games_resp = requests.get(
            "https://api.balldontlie.io/v1/games",
            params={"league": "nhl", "dates[]": today},
            headers=headers
        )
        games_resp.raise_for_status()
        games_data = games_resp.json().get("data", [])
        games_summary = json.dumps([{"home": g["home_team"]["full_name"], "away": g["visitor_team"]["full_name"], "time": g.get("status")} for g in games_data])

        def extract_tables(url):
            try:
                tables = pd.read_html(url)
                return "\n\n".join([df.to_string(index=False, header=True) for df in tables[:10]])
            except:
                return "Error or no tables."

        def extract_text(url):
            try:
                html = requests.get(url).text
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text(separator='\n', strip=True)[:15000]
            except:
                return "Error fetching."

        matchup_text = extract_text("https://www.dailyfantasyfuel.com/nhl/matchup-analysis/")
        lineups_text = extract_text("https://www.dailyfantasyfuel.com/nhl/starting-lineups/")
        ga_text = extract_tables("https://shotpropz.com/nhl/goals-against-by-position/")
        sog_text = extract_tables("https://shotpropz.com/nhl/sog-against-by-position/")
        team_def_text = extract_tables("https://shotpropz.com/nhl/team-defensive-stat-overview/")
        team_off_text = extract_tables("https://shotpropz.com/nhl/team-offensive-stat-overview/")
        statmuse_text = extract_text("https://www.statmuse.com/nhl/ask/nhl-scoring-leaders-last-7-games-this-season")

        cumulative_prompt = f"""
Let’s put together an anytime goal scorer and SOG list based only on the provided data. No assumptions, no fillers – purely data-driven.

Step 1: Today's matchups:
{games_summary}
{matchup_text}

Step 2: Lineups/goalies:
{lineups_text}

Step 3: Goals against by position:
{ga_text}

Step 4: SOG against by position:
{sog_text}

Step 5: Team defense:
{team_def_text}

Step 6: Team offense:
{team_off_text}

Step 7: Recent scoring:
{statmuse_text}

Output ONLY valid JSON:
{{
  "sog_props": [{{"player": "", "team": "", "opponent": "", "projected_sog": 0.0, "confidence": 0, "reasoning": ""}}],
  "atg_props": [{{"player": "", "team": "", "opponent": "", "projected_prob": 0, "confidence": 0, "reasoning": ""}}]
}}
Top 10-15 each, sorted by confidence descending (0-100).
"""

        grok_resp = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROK_API_KEY}"},
            json={
                "model": "grok-4",
                "messages": [{"role": "user", "content": cumulative_prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }
        )
        grok_resp.raise_for_status()
        result = grok_resp.json()["choices"][0]["message"]["content"]
        props_json = json.loads(result)

        return props_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
