# --- fpl_optimizer.py ---
import pandas as pd
import requests
from pulp import *
from config import TEAM_ID, SHEET_NAME, N_WEEKS
from sheets_output import write_plan_to_sheets

# Pull player and fixture data
def fetch_fpl_data():
    r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    data = r.json()
    players = pd.DataFrame(data['elements'])
    teams = pd.DataFrame(data['teams'])
    positions = pd.DataFrame(data['element_types'])
    return players, teams, positions

def get_expected_points(row, gw):
    # 'ep_next' is FPL's projection for next GW, fallback to 'form'
    return float(row['ep_next']) if row['ep_next'] else float(row['form'])

def optimize_one_week(players, teams, positions, budget, squad_size=15, club_limit=3, position_limits={1:2,2:5,3:5,4:3}):
    prob = LpProblem("FPL", LpMaximize)
    choices = LpVariable.dicts("pick", players.index, 0, 1, LpBinary)
    prob += lpSum([choices[i] * players.loc[i, 'xP'] for i in players.index])
    prob += lpSum([choices[i] * players.loc[i, 'now_cost']/10 for i in players.index]) <= budget
    prob += lpSum([choices[i] for i in players.index]) == squad_size
    for team_id in teams['id']:
        prob += lpSum([choices[i] for i in players.index if players.loc[i, 'team'] == team_id]) <= club_limit
    for pos_id, limit in position_limits.items():
        prob += lpSum([choices[i] for i in players.index if players.loc[i, 'element_type'] == pos_id]) == limit
    prob.solve()
    selected = [i for i in players.index if choices[i].varValue == 1]
    return players.loc[selected].copy()

def rolling_horizon_optimizer(N_WEEKS=3):
    budget = 100.0
    club_limit = 3
    squad_size = 15
    position_limits = {1:2,2:5,3:5,4:3}
    players, teams, positions = fetch_fpl_data()
    # Use only top 40 by xP for speed
    players['xP'] = players.apply(get_expected_points, axis=1, args=(1,))
    players = players.sort_values("xP", ascending=False).head(40).reset_index(drop=True)
    weekly_plans = []
    squads_by_week = []
    current_squad = []
    in_bank = 0.0
    chips = ["WC", "BB", "FH", "TC"] # simple placeholder
    for gw in range(1,N_WEEKS+1):
        squad = optimize_one_week(players, teams, positions, budget, squad_size, club_limit, position_limits)
        # Simulate 1 FT; swap lowest xP for highest not owned
        if current_squad:
            owned_ids = set([p["id"] for p in current_squad])
            new_ids = set(squad["id"])
            outs = [p for p in current_squad if p["id"] not in new_ids]
            ins = squad[~squad["id"].isin(owned_ids)]
        else:
            outs = []
            ins = squad
        cap = squad.loc[squad['xP'].idxmax()]
        weekly_plans.append({
            "GW": gw,
            "transfers_out": [o["name"] if isinstance(o,dict) else o for o in outs][:1],
            "transfers_in": [row["web_name"] for idx, row in ins.iterrows()][:1],
            "chip": "",
            "captain": cap["web_name"],
            "xp": squad["xP"].sum() + cap["xP"]
        })
        squads_by_week.append([
            {
                "pos": positions.loc[positions['id']==row['element_type'],'singular_name_short'].values[0],
                "name": row["web_name"],
                "team": teams.loc[teams['id']==row['team'],'name'].values[0],
                "xp": row["xP"],
                "id": row["id"]
            }
            for idx, row in squad.iterrows()
        ])
        current_squad = squads_by_week[-1]
    return weekly_plans, squads_by_week

if __name__ == "__main__":
    plans, squads = rolling_horizon_optimizer(N_WEEKS)
    write_plan_to_sheets(SHEET_NAME, plans, squads)
    print("FPL optimization complete and written to Google Sheets.")
