import pandas as pd
import requests
from pulp import *
from config import TEAM_ID, N_WEEKS, MAX_HITS_PER_GW
from get_fpl_team import fetch_user_team
from understat_xp import get_understat_xgxa
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
    players['norm_name'] = players['web_name'].str.lower().str.replace('.', '', regex=False).str.replace('-', ' ', regex=False).str.replace('_', ' ', regex=False).str.strip()
    if not understat_df.empty:
        understat_df['norm_name'] = understat_df['web_name'].str.lower().str.replace('.', '', regex=False).str.replace('-', ' ', regex=False).str.replace('_', ' ', regex=False).str.strip()
        merged = pd.merge(players, understat_df, how='left', left_on='norm_name', right_on='norm_name', suffixes=('', '_us'))
        merged['xP_final'] = merged['xP'].fillna(merged['ep_next'].astype(float))
    else:
        merged = players
        merged['xP_final'] = merged['ep_next'].astype(float)
    return merged

def get_current_team_ids(picks):
    return [p['element'] for p in picks]

def squad_points(squad, captain_id):
    base = squad["xP_final"].sum()
    cap = squad[squad["id"] == captain_id]["xP_final"].values[0] if captain_id in squad["id"].values else 0
    return base + cap

def optimize_transfers(squad_ids, bank, players, teams, positions, understat_df, allowed_transfers=1, max_hits=1):
    current_team = players[players["id"].isin(squad_ids)].copy()
    possible_ins = players[~players["id"].isin(squad_ids)].copy().sort_values("xP_final", ascending=False)
    best_move = {"score": -999, "outs": [], "ins": [], "new_squad": squad_ids}
    for ntransfers in range(1, allowed_transfers + max_hits + 1):
        outs_combos = list(itertools.combinations(squad_ids, ntransfers))
        ins_combos = list(itertools.combinations(possible_ins["id"].tolist(), ntransfers))
        for outs in outs_combos:
            for ins in ins_combos:
                new_ids = list((set(squad_ids) - set(outs)) | set(ins))
                if len(new_ids) != 15:
                    continue
                new_squad = players[players["id"].isin(new_ids)]
                cost = new_squad["now_cost"].sum() / 10
                if cost > 100 + bank:
                    continue
                score = new_squad["xP_final"].sum()
                if score > best_move["score"]:
                    best_move = {"score": score, "outs": outs, "ins": ins, "new_squad": new_ids}
        if best_move["score"] > -999:
            break
    return best_move

def best_xi_for_gw(players, teams, positions):
    prob = LpProblem("BestXI", LpMaximize)
    choices = LpVariable.dicts("pick", players.index, 0, 1, LpBinary)
    budget = 100.0
    squad_size = 15
    club_limit = 3
    position_limits = {1:2,2:5,3:5,4:3}
    prob += lpSum([choices[i] * players.loc[i, 'xP_final'] for i in players.index])
    prob += lpSum([choices[i] * players.loc[i, 'now_cost']/10 for i in players.index]) <= budget
    prob += lpSum([choices[i] for i in players.index]) == squad_size
    for team_id in teams['id']:
        prob += lpSum([choices[i] for i in players.index if players.loc[i, 'team'] == team_id]) <= club_limit
    for pos_id, limit in position_limits.items():
        prob += lpSum([choices[i] for i in players.index if players.loc[i, 'element_type'] == pos_id]) == limit
    prob.solve()
    selected = [i for i in players.index if choices[i].varValue == 1]
    return players.loc[selected].copy()

if __name__ == "__main__":
    picks, bank, chips_available = fetch_user_team(TEAM_ID)
    players, teams, positions = fetch_fpl_data()
    understat_df = get_understat_xgxa()
    players = merge_xgxa(players, understat_df)
    squad_ids = get_current_team_ids(picks)
    transfer_plans = []
    best_xi_list = []
    current_ids = squad_ids[:]
    current_bank = bank
    for gw in range(1, N_WEEKS+1):
        move = optimize_transfers(current_ids, current_bank, players, teams, positions, understat_df, allowed_transfers=1, max_hits=MAX_HITS_PER_GW)
        new_ids = move["new_squad"]
        squad_df = players[players["id"].isin(new_ids)]
        captain_id = squad_df.sort_values("xP_final", ascending=False).iloc[0]["id"]
        captain_name = squad_df[squad_df["id"]==captain_id]["web_name"].values[0]
        ft_hit = "1FT" if len(move["outs"]) == 1 else "1FT+Hit"
        transfer_plans.append({
            "GW": gw,
            "transfers_out": [players[players["id"]==oid]["web_name"].values[0] for oid in move["outs"]],
            "transfers_in": [players[players["id"]==iid]["web_name"].values[0] for iid in move["ins"]],
            "ft_hit": ft_hit,
            "captain": captain_name,
            "xp": squad_points(squad_df, captain_id),
            "chip": ""  # Fill manually if playing a chip
        })
        current_ids = new_ids
        best_xi = best_xi_for_gw(players, teams, positions)
        xi_list = [{
            "pos": positions.loc[positions['id']==row['element_type'],'singular_name_short'].values[0],
            "name": row["web_name"],
            "team": teams.loc[teams['id']==row['team'],'name'].values[0],
            "xp": row["xP_final"]
        } for idx, row in best_xi.iterrows()]
        best_xi_list.append(xi_list)

    # --- WRITE TO CSV FILES ---
    # 1. Transfer Plan
    tp_df = pd.DataFrame(transfer_plans)
    # For nice CSV, join the lists:
    tp_df["transfers_out"] = tp_df["transfers_out"].apply(lambda x: ", ".join(x))
    tp_df["transfers_in"] = tp_df["transfers_in"].apply(lambda x: ", ".join(x))
    tp_df.to_csv("transfer_plan.csv", index=False)

    # 2. Best XI
    flat = []
    for gw, xi in enumerate(best_xi_list, 1):
        for row in xi:
            row2 = row.copy()
            row2['GW'] = gw
            flat.append(row2)
    pd.DataFrame(flat).to_csv("best_possible_xi.csv", index=False)

    print("CSV output complete. Files: transfer_plan.csv, best_possible_xi.csv")
