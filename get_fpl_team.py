# --- get_fpl_team.py ---
import requests
import os

def fetch_user_team(team_id):
    cookies = {"PL_PROFILE": os.environ["FPL_SESSION_COOKIE"]}
    url = f"https://fantasy.premierleague.com/api/my-team/{team_id}/"
    r = requests.get(url, cookies=cookies)
    if r.status_code != 200:
        raise Exception(f"Failed to fetch FPL team! Check session cookie. Status: {r.status_code}, Msg: {r.text}")
    data = r.json()
    picks = data["picks"]
    bank = data["transfers"]["bank"] / 10.0  # tenths of a million
    transfers = data["transfers"]["limit"]
    chips_available = [chip for chip in data.get("chips", []) if chip["played"] is False]
    # Returns: list of dicts: [{element: player_id, position: slot, is_captain: True/False, is_vice_captain: True/False}]
    return picks, bank, chips_available
