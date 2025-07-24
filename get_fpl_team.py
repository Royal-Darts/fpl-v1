# --- get_fpl_team.py ---
import pandas as pd
import re

def extract_player_name(cell):
    # For example: "A.BeckerLiverpoolGKP" -> "A.Becker"
    m = re.match(r"([A-Za-z\.\- ]+?)([A-Z][a-z]+)?(GKP|DEF|MID|FWD)?$", str(cell).strip())
    if m:
        name = m.group(1).strip()
        return name
    # Fallback: remove trailing uppercase position, team
    name = re.split(r'[A-Z]{2,}', str(cell).strip())[0].strip()
    return name

def fetch_user_team(team_id=None):
    # Read your Excel file directly
    df = pd.read_excel("FPL Optimizer.xlsx", header=None)
    # Find player name cells: skip header rows, only take the combined name cells
    player_cells = []
    for col in range(df.shape[1]):
        for val in df[col]:
            if pd.isnull(val):
                continue
            sval = str(val)
            # Ignore position headers
            if sval in ["Goalkeepers", "Defenders", "Midfielders", "Forwards"]:
                continue
            # Ignore prices, scores, and blank/short cells
            if sval.startswith("£") or sval.isdigit() or len(sval) < 3:
                continue
            # Only take first column in each player row
            player_cells.append(sval)
    # Remove duplicates (in case of formatting)
    player_cells = list(dict.fromkeys(player_cells))

    # Only take the first 15 players (top-down, matches FPL layout)
    player_cells = player_cells[:15]

    # Extract names
    player_names = [extract_player_name(cell) for cell in player_cells if extract_player_name(cell)]

    # Map names to FPL element IDs using the latest FPL bootstrap-static
    import requests
...
fpl_data = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
fpl_players = pd.DataFrame(fpl_data['elements'])

    squad_ids = []
    for name in player_names:
        match = fpl_players[fpl_players['web_name'].str.lower().str.replace('.', '', regex=False) == name.lower().replace('.', '')]
        if not match.empty:
            squad_ids.append(int(match.iloc[0]['id']))
        else:
            # Try partial match as fallback (robust to minor naming issues)
            best = fpl_players[fpl_players['web_name'].str.lower().str.contains(name.lower().replace('.', ''))]
            if not best.empty:
                squad_ids.append(int(best.iloc[0]['id']))
            else:
                print(f"Could not match name: {name} (check spelling or FPL web_name)")

    if len(squad_ids) != 15:
        print(f"Warning: Found {len(squad_ids)} player IDs, not 15. Please verify your names!")

    picks = [{"element": id} for id in squad_ids]
    bank = 0.0  # Enter your actual ITB if you want, or leave at 0.0
    chips_available = []
    return picks, bank, chips_available
