# --- sheets_output.py ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def get_gsheets_client():
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        raise Exception("GOOGLE_CREDENTIALS not found in environment.")
    creds_dict = json.loads(creds_json)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def write_transfer_plan(sheet_name, transfer_plans):
    client = get_gsheets_client()
    try:
        ss = client.open(sheet_name)
    except Exception as e:
        raise Exception(f"Could not open sheet '{sheet_name}': {e}")
    # Transfer Plan Tab
    ws_title = "Transfer Plan"
    if ws_title in [ws.title for ws in ss.worksheets()]:
        ss.worksheet(ws_title).clear()
        plan_ws = ss.worksheet(ws_title)
    else:
        plan_ws = ss.add_worksheet(title=ws_title, rows="100", cols="10")
    headers = ["GW", "Transfers Out", "Transfers In", "FT/Hits Used", "Captain", "Exp. Points", "Chip (Manual)"]
    plan_ws.append_row(headers)
    for week in transfer_plans:
        plan_ws.append_row([
            week["GW"],
            ', '.join(week["transfers_out"]),
            ', '.join(week["transfers_in"]),
            week["ft_hit"],
            week["captain"],
            round(week["xp"],2),
            week["chip"] if week.get("chip") else ""
        ])

def write_best_xi(sheet_name, best_xi_list):
    client = get_gsheets_client()
    try:
        ss = client.open(sheet_name)
    except Exception as e:
        raise Exception(f"Could not open sheet '{sheet_name}': {e}")
    ws_title = "Best Possible XI"
    if ws_title in [ws.title for ws in ss.worksheets()]:
        ss.worksheet(ws_title).clear()
        xi_ws = ss.worksheet(ws_title)
    else:
        xi_ws = ss.add_worksheet(title=ws_title, rows="200", cols="10")
    xi_ws.append_row(["GW", "Pos", "Player", "Team", "xP"])
    for gw, squad in enumerate(best_xi_list, 1):
        for p in squad:
            xi_ws.append_row([
                gw, p["pos"], p["name"], p["team"], round(p["xp"],2)
            ])
