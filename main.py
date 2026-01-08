import requests
from fastapi import FastAPI, HTTPException
from datetime import datetime

app = FastAPI()

# Your SportsRadar trial key (filled in for copy-paste – move to env var later)
SPORTSRADAR_KEY = "hEs9yyywRrsJhThoxlTJja66BOYVb2411RvoGPjh"

@app.get("/")
def get_daily_props():
    try:
        DAILY_JSON_URL = "https://raw.githubusercontent.com/beelobeatz/nhl-prop-backend/main/daily_atg_picks.json"
        resp = requests.get(DAILY_JSON_URL, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except:
        return {"matchups": [], "note": "Check daily JSON"}

@app.get("/live")
def get_live_stats():
    try:
        today = datetime.utcnow().strftime('%Y/%m/%d')
        base_url = "https://api.sportradar.us/nhl/trial/v8/en"
        schedule_url = f"{base_url}/games/{today}/schedule.json?api_key={SPORTSRADAR_KEY}"
        schedule = requests.get(schedule_url).json().get("games", [])

        live_sog = []
        live_goals = []

        for game in schedule:
            if game.get("status") in ["inprogress", "halftime", "closed"]:
                game_id = game["id"]
                boxscore_url = f"{base_url}/games/{game_id}/boxscore.json?api_key={SPORTSRADAR_KEY}"
                boxscore = requests.get(boxscore_url).json()

                game_str = f"{game['away']['abbr']} @ {game['home']['abbr']} ({game.get('scoring', {}).get('summary', 'Live')})"

                for team in ["home", "away"]:
                    players = boxscore.get(team, {}).get("players", [])
                    for player in players:
                        stats = player.get("statistics", {})
                        name = player.get("full_name")
                        team_abbr = game[team]["abbr"]
                        sog = stats.get("shots", 0)
                        goals = stats.get("goals", 0)

                        live_sog.append({"player": name, "team": team_abbr, "sog": sog, "game": game_str})
                        live_goals.append({"player": name, "team": team_abbr, "goals": goals, "game": game_str})

        live_sog = sorted(live_sog, key=lambda x: x["sog"], reverse=True)[:10]
        live_goals = sorted(live_goals, key=lambda x: x["goals"], reverse=True)[:10]

        return {"top_sog": live_sog, "top_goals": live_goals}

    except Exception as e:
        return {"error": str(e), "top_sog": [], "top_goals": []}
