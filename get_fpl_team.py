# --- get_fpl_team.py ---
import requests
import os

def fetch_user_team(team_id):
    token = os.environ["FPL_API_TOKEN"]  # Set this as a GitHub secret
    url = f"https://fantasy.premierleague.com/api/my-team/{team_id}/"
    headers = {
        "x-api-authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception(f"Failed to fetch FPL team! Check token. Status: {r.status_code}, Msg: {r.text}")
    data = r.json()
    picks = data["picks"]
    bank = data["transfers"]["bank"] / 10.0  # tenths of a million
    transfers = data["transfers"]["limit"]
    chips_available = [chip for chip in data.get("chips", []) if chip.get("played", False) is False]
    return picks, bank, chips_available
