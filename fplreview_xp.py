import requests
import pandas as pd

def get_fplreview_xp():
    url = "https://fplreview.com/api/planner/projections/latest"
    r = requests.get(url)
    r.raise_for_status()
    raw = r.json()
    # The key is "players", which is a dict keyed by FPL player ID (as str)
    data = []
    for k, v in raw["players"].items():
        # keys: id, name, position, team, xPts, mins, etc.
        data.append({
            "id": int(k),
            "web_name": v.get("name", ""),
            "xPts": v.get("xPts", 0),
            "mins": v.get("mins", 0),
            # Add more fields if desired!
        })
    df = pd.DataFrame(data)
    return df
