# --- understat_xp.py ---
from understatapi import UnderstatClient
import pandas as pd

def get_understat_xgxa(current_season=2024):
    uc = UnderstatClient()
    players = uc.get_league_players("EPL", current_season)
    df = pd.DataFrame([{
        "web_name": p.player_name,
        "xG": p.xg,
        "xA": p.xa,
        "games": p.matches,
        "id": int(p.id)
    } for p in players])
    df["xP"] = (df["xG"]*4 + df["xA"]*3) / df["games"].replace(0, 1)  # crude xP: goals*4, assists*3
    return df
