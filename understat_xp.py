# --- understat_xp.py ---
import pandas as pd
import asyncio
from understat import Understat
import aiohttp
import nest_asyncio

nest_asyncio.apply()  # So we can run asyncio in GitHub Actions or Jupyter

def normalize_name(name):
    return name.lower().replace('.', '').replace('-', ' ').replace('_', ' ').strip()

async def fetch_understat_data(season=2024):
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        players_data = await understat.get_league_players("EPL", season)
        # Each player_data: dict with keys like 'id', 'player_name', 'xG', 'xA', 'games'
        players = []
        for p in players_data:
            players.append({
                "web_name": normalize_name(p['player_name']),
                "xG": float(p.get('xG', 0)),
                "xA": float(p.get('xA', 0)),
                "games": int(p.get('games', 1)),
                "id": int(p.get('id', 0)),
            })
        df = pd.DataFrame(players)
        # Crude xP (can be improved): (xG*4 + xA*3)/games
        df["xP"] = (df["xG"]*4 + df["xA"]*3) / df["games"].replace(0, 1)
        return df

def get_understat_xgxa(current_season=2024):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        df = loop.run_until_complete(fetch_understat_data(current_season))
        return df
    except Exception as e:
        print("Understat fetch failed, falling back to empty DataFrame. Error:", e)
        return pd.DataFrame(columns=["web_name", "xG", "xA", "games", "id", "xP"])
