# --- get_fpl_team.py ---
import pandas as pd
import re
import requests

def extract_player_name(cell):
    # e.g., "A.BeckerLiverpoolGKP" → "A.Becker"
    m = re.match(r"([A-Za-z\.\- ]+?)([A-Z][a-z]+)?(GKP|DEF|MID|FWD)?$", str(cell).strip())
    if m:
        name = m.group(1).strip()
        return name
    # Fallback: remove trailing uppercase position, team
    name = re.split(r'[A-Z]{2,}', str(cell).strip())[0].strip()
    return name

def fetch_user_team(team_id=None):
    # Read your Excel file
    df = pd.read_excel("FPL Optimizer.xlsx", header=None)
    player_cells = []
    for col in range(df.shape[1]):
        for val in df[col]:
            if pd.isnull(val):
                continue
            sval = str(val)
            if sval in ["Goalkeepers", "Defenders", "Midfielders", "Forwards"]:
                continue
            if sval.startswith("£") or sval.isdigit() or len(sval) < 3:
                continue
            player_cells.append(sval)
    # Remove duplicates, keep order
    player_cells = list(dict.fromkeys(player_cells))
    # Only take the first 15 players
    player_cells = player_cells[:15]
    player_names = [extract_player_name(cell) for cell in player_cells if extract_player_name(cell)]

    # Get FPL player data safely
    fpl_data = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
    fpl_players = pd.DataFrame(fpl_data['elements'])

    squad_ids = []
    for name in player_names:
        match = fpl_players[fpl_players['web_name'].str.lower().str.replace('.', '', regex=False) == name.lower().replace('.', '')]
        if not match.empty:
            squad_ids.append(int(match.iloc[0]['id']))
        else:
            best = fpl_players[fpl_players['web_name'].str.lower().str.contains(name.lower().replace('.', ''))]
            if not best.empty:
                squad_ids.append(int(best.iloc[0]['id']))
            else:
                print(f"Could not match name: {name} (check spelling or FPL web_name)")
    if len(squad_ids) != 15:
        print(f"Warning: Found {len(squad_ids)} player IDs, not 15. Please verify your names!")

    picks = [{"element": id} for id in squad_ids]
    bank = 0.0  # Set your ITB here if you want
    chips_available = []
    return picks, bank, chips_available
