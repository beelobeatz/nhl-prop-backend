import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def get_daily_props():
    try:
        # Your hosted JSON URL (update this when you upload new picks)
        DAILY_JSON_URL = "https://raw.githubusercontent.com/beelobeatz/nhl-prop-backend/main/daily_atg_picks.json"

        resp = requests.get(DAILY_JSON_URL, timeout=10)
        resp.raise_for_status()
        props_json = resp.json()

        # Fallback if empty
        if not props_json.get("atg_props"):
            return {"atg_props": [], "note": "Update daily JSON for latest elite picks"}

        return props_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
