import requests
import pandas as pd
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpBinary, value

FPL_API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
POSITION_MAP = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
POS_COUNTS = {'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}

def fetch_fpl_data():
    data = requests.get(FPL_API_URL).json()
    players = pd.DataFrame(data['elements'])
    teams = pd.DataFrame(data['teams'])
    player_team_map = dict(zip(teams['id'], teams['name']))
    players['team_name'] = players['team'].map(player_team_map)
    players['pos'] = players['element_type'].map(POSITION_MAP)
    players['now_cost'] = players['now_cost'] / 10
    players['id'] = players['id'].astype(int)
    players['web_name'] = players['web_name']
    return players

def fetch_projection(csv_path=None, players=None, n_gw=5):
    if csv_path is None:
        # Fallback: use form as points
        for gw in range(1, n_gw+1):
            players[f'exp_gw{gw}'] = players['form'].astype(float).fillna(2.0)
        return players
    proj = pd.read_csv(csv_path)
    # Must have: id, web_name, pos, team_name, now_cost, exp_gw1, exp_gw2, ...
    return proj

def optimize_gw(players, gw, prev_squad=None, free_transfers=1, budget=100.0, chips=None):
    n = players.shape[0]
    prob = LpProblem(f"FPL_GW{gw}", LpMaximize)
    x = LpVariable.dicts("pick", (i for i in range(n)), 0, 1, LpBinary)
    starting = LpVariable.dicts("start", (i for i in range(n)), 0, 1, LpBinary)
    cap = LpVariable.dicts("cap", (i for i in range(n)), 0, 1, LpBinary)
    vice = LpVariable.dicts("vice", (i for i in range(n)), 0, 1, LpBinary)
    # Squad constraints
    for pos, count in POS_COUNTS.items():
        prob += lpSum([x[i] for i in range(n) if players.iloc[i]['pos']==pos]) == count
    prob += lpSum([x[i] for i in range(n)]) == 15
    prob += lpSum([x[i] * players.iloc[i]['now_cost'] for i in range(n)]) <= budget
    for team in players['team_name'].unique():
        prob += lpSum([x[i] for i in range(n) if players.iloc[i]['team_name']==team]) <= 3
    # XI constraints
    prob += lpSum([starting[i] for i in range(n)]) == 11
    prob += lpSum([starting[i] for i in range(n) if players.iloc[i]['pos']=='GK']) == 1
    prob += lpSum([starting[i] for i in range(n) if players.iloc[i]['pos']=='DEF']) >= 3
    prob += lpSum([starting[i] for i in range(n) if players.iloc[i]['pos']=='MID']) >= 2
    prob += lpSum([starting[i] for i in range(n) if players.iloc[i]['pos']=='FWD']) >= 1
    for i in range(n):
        prob += starting[i] <= x[i]
    # Captain/vice
    prob += lpSum([cap[i] for i in range(n)]) == 1
    prob += lpSum([vice[i] for i in range(n)]) == 1
    for i in range(n):
        prob += cap[i] <= starting[i]
        prob += vice[i] <= starting[i]
        prob += cap[i] + vice[i] <= 1
    # Transfers
    transfers = None
    hits = 0
    if prev_squad is not None:
        old_set = set(prev_squad)
        new_vars = [players.iloc[i]['id'] for i in range(n)]
        outs = [i for i in range(n) if players.iloc[i]['id'] in old_set and value(x[i]) < 0.5]
        ins = [i for i in range(n) if players.iloc[i]['id'] not in old_set and value(x[i]) > 0.5]
        n_transfers = len(outs)
        hits = max(0, n_transfers - free_transfers)*4
        # Not solved yet, so we define n_transfers as a var:
        n_out = lpSum([1-x[i] if players.iloc[i]['id'] in old_set else 0 for i in range(n)])
        prob += n_out <= 15
    # Chips logic (very simple)
    bench_pts = 0
    if chips and "Bench Boost" in chips:
        bench_pts = lpSum([x[i]*(1-starting[i])*players.iloc[i][f'exp_gw{gw}'] for i in range(n)])
    # Objective
    main_pts = lpSum([
        starting[i]*players.iloc[i][f'exp_gw{gw}'] +
        cap[i]*players.iloc[i][f'exp_gw{gw}']  # Captain double
        for i in range(n)
    ])
    prob.setObjective(main_pts + bench_pts - hits)
    prob.solve()
    picked = [i for i in range(n) if value(x[i])>0.5]
    xi = [i for i in range(n) if value(starting[i])>0.5]
    cap_i = [i for i in range(n) if value(cap[i])>0.5]
    vice_i = [i for i in range(n) if value(vice[i])>0.5]
    squad = players.iloc[picked].copy()
    squad['Starting'] = squad.index.isin(xi)
    squad['Captain'] = squad.index.isin(cap_i)
    squad['Vice'] = squad.index.isin(vice_i)
    return {
        "squad": squad,
        "xi": xi,
        "cap": cap_i,
        "vice": vice_i,
        "expected_points": value(prob.objective),
        "hits": hits,
        "transfers": None  # For full transfer logic, store outs/ins above after solving
    }

def rolling_horizon(players, start_gw=1, n_gw=5, start_squad=None, budget=100.0, free_transfers=1, chips=None):
    squad = start_squad
    gw_logs = []
    rem_budget = budget
    rem_fts = free_transfers
    used_chips = set()
    for gwi in range(start_gw, start_gw+n_gw):
        gwchips = [c for c in (chips or []) if c not in used_chips]
        res = optimize_gw(players, gwi, prev_squad=squad, free_transfers=rem_fts, budget=rem_budget, chips=gwchips)
        gw_logs.append({
            "gw": gwi,
            "squad": res["squad"],
            "expected_points": res["expected_points"],
            "captain": res["squad"].loc[res["squad"]['Captain'], "web_name"].tolist(),
            "bench": res["squad"].loc[~res["squad"]['Starting'], "web_name"].tolist(),
            "hits": res["hits"]
        })
        squad = res["squad"]['id'].tolist()
        rem_fts = 1  # After GW1, 1 FT per week (FPL rule; can extend to 2 if not used)
        # Chips: very simple one-per-season logic, can be extended
        used_chips.update(gwchips)
    return gw_logs
