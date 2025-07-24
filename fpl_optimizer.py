# --- fpl_optimizer.py ---
import pandas as pd
import requests
from pulp import *
from config import TEAM_ID, SHEET_NAME, N_WEEKS, MAX_HITS_PER_GW
from get_fpl_team import fetch_user_team
from understat_xp import get_understat_xgxa
from sheets_output import write_transfer_plan, write_best_xi
import itertools

def fetch_fpl_data():
    r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    data = r.json()
    players = pd.DataFrame(data['elements'])
    teams = pd.DataFrame(data['teams'])
    positions = pd.DataFrame(data['element_types'])
    return players, teams, positions

def merge_xgxa(players, understat_df):
    players = players.copy()
    players['web_name'] = players['web_name'].str.lower()
    understat_df['web_name'] = understat_df['web_name'].str.lower()
    merged = pd.merge(players, understat_df, how='left', on='web_name', suffixes=('', '_us'))
    merged['xP_final'] = merged['xP'].fillna(merged['ep_next'].astype(float))
    return merged

def get_current_team_ids(picks):
    return [p['element'] for p in picks]

def squad_points(squad, captain_id):
    base = squad["xP_final"].sum()
    cap = squad[squad["id"] == captain_id]["xP_final"].values[0] if captain_id in squad["id"].values else 0
    return base + cap

def optimize_transfers(squad_ids, bank, players, teams, positions, understat_df, allowed_transfers=1, max_hits=1):
    # This function can be made more advanced but keeps things simple for now
    current_team = players[players["id"].isin(squad_ids)].copy()
    possible_ins = players[~players["id"].isin(squad_ids)].copy().sort_values("xP_final", ascending=False)
    best_move = {"score": -999, "outs": [], "ins": [], "new_squad": squad_ids}
    for ntransfers in range(1, allowed_transfers + max_hits + 1):
        outs_combos = list(itertools.combinations(squad_ids, ntransfers))
        ins_combos = list(itertools.combinations(possible_ins["id"].t
