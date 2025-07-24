# --- sheets_output.py ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
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

def write_plan_to_sheets(sheet_name, weekly_plans, squads_by_week):
    client = get_gsheets_client()
    try:
        ss = client.open(sheet_name)
    except Exception as e:
        raise Exception(f"Could not open sheet '{sheet_name}': {e}")
    # Weekly Plan Tab
    if "GW Plan" in [ws.title for ws in ss.worksheets()]:
        ss.worksheet("GW Plan").clear()
        plan_ws = ss.worksheet("GW Plan")
    else:
        plan_ws = ss.add_worksheet(title="GW Plan", rows="100", cols="10")
    headers = ["GW", "Transfers Out", "Transfers In", "Chip", "Captain", "Total xP"]
    plan_ws.append_row(headers)
    for week in weekly_plans:
        plan_ws.append_row([
            week["GW"],
            ', '.join(week["transfers_out"]),
            ', '.join(week["transfers_in"]),
            week["chip"] if week["chip"] else "",
            week["captain"],
            round(week["xp"],2)
        ])
    # Squad By Week Tab
    if "Squad By Week" in [ws.title for ws in ss.worksheets()]:
        ss.worksheet("Squad By Week").clear()
        squad_ws = ss.worksheet("Squad By Week")
    else:
        squad_ws = ss.add_worksheet(title="Squad By Week", rows="500", cols="10")
    squad_ws.append_row(["GW", "Pos", "Player", "Team", "xP"])
    for gw, squad in enumerate(squads_by_week, 1):
        for p in squad:
            squad_ws.append_row([
                gw, p["pos"], p["name"], p["team"], round(p["xp"],2)
            ])
