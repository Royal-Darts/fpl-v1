# FPL Optimizer (Tokvam Model, Multi-Week, Google Sheets, Fully Automated)

## 1. Setup Google Sheets and Google Cloud

- Create a Google Sheet named: **FPL Optimizer**
- Go to https://console.developers.google.com/
    - Create a project, enable **Google Sheets API**
    - Create a **service account**, download `credentials.json`
    - Find your service account email, share your sheet (Editor) with it

## 2. Set Up GitHub Repo

- Create a new repo, upload all files from this repo.
- Go to Settings > Secrets > Actions > New repository secret
    - Name: `GOOGLE_CREDENTIALS`
    - Paste the **contents** of your `credentials.json` (all text, not the file itself)
- Commit/push all code.

## 3. How it works

- **Every Friday (or on-demand), GitHub Actions runs the optimizer**
- **Optimized plans, transfers, chip, captain picks for next 3 GWs go to your Google Sheet**

## 4. Config

- Edit `config.py` with your TEAM_ID, SHEET_NAME, N_WEEKS (planning window)

## 5. Advanced/Extending

- Code is modular: extend to use Understat, FBref, or your own data
- Streamlit web dashboard ready: just add a file, point to the same Sheet

---

## Support

If you have any issues, copy errors here or ping ChatGPT for fixes!
