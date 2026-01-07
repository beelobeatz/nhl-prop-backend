import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def get_daily_props():
    try:
        # Raw GitHub URL for your daily JSON (auto updates when you commit)
        DAILY_JSON_URL = "https://raw.githubusercontent.com/beelobeatz/nhl-prop-backend/main/daily_atg_picks.json"

        resp = requests.get(DAILY_JSON_URL, timeout=10)
        resp.raise_for_status()
        props_json = resp.json()

        return props_json or {"atg_props": [], "note": "Update daily JSON for latest picks"}

    except Exception as e:
        return {"error": str(e), "atg_props": [], "note": "Check JSON file"}
