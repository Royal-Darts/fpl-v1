# FPL Optimizer – Advanced (Live Transfers, Understat xG, Google Sheets)

## 1. Google Sheets Setup

- Sheet shared with Google Service Account, Google Sheets API/Drive API enabled.

## 2. FPL API Token Setup

To fetch your actual team, you need your **x-api-authorization Bearer token**:
1. Log into [https://fantasy.premierleague.com/](https://fantasy.premierleague.com/) in your browser.
2. Open Dev Tools > Network tab.
3. Reload the page and look for an API call (e.g., `/api/my-team/410700/`).
4. Click the request, and in Request Headers, copy the value after `x-api-authorization: Bearer ` (it's a long string).
5. In your repo, go to **Settings > Secrets > Actions > New repository secret**
    - Name: `FPL_API_TOKEN`
    - Value: (paste the full Bearer token)

**Do NOT share your token or commit it to code.**

## 3. Push All Code

- Create all files as above. Commit and push to your repo.

## 4. Running

- Go to GitHub Actions tab, select "FPL Optimize and Push to Sheets" > Run workflow (manual run).
- Sheet will update in ~1–2 min if all is correct.

## 5. Sheet Output

- **Transfer Plan**: Recommended moves from your live team, each GW.
- **Best Possible XI**: Free Hit squad each GW for comparison.

## 6. Chip Usage

- **Manual**: The optimizer will not auto-play chips. Fill "Chip (Manual)" column in Google Sheet if you want to play one that week.

## 7. FAQ

- **Q: Workflow fails?**
    - Check secrets: both `GOOGLE_CREDENTIALS` and `FPL_API_TOKEN` must be present.
    - Double-check Google Sheet sharing.
    - Paste error in chat for help.

---

This system is modular. To add features (e.g., Telegram alerts, advanced projections), extend code as desired!
