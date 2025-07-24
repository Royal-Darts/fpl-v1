# --- fplreview_xp.py ---
import requests
import pandas as pd

def get_fplreview_xp():
    url = "https://fplreview.com/api/planner/projections/latest"
    try:
        r = requests.get(url)
        r.raise_for_status()
        raw = r.json()
        data = []
        for k, v in raw["players"].items():
            data.append({
                "id": int(k),
                "web_name": v.get("name", ""),
                "xPts": v.get("xPts", 0),
                "mins": v.get("mins", 0),
            })
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"FPL Review API not available (using FPL ep_next). Reason: {e}")
        return None
