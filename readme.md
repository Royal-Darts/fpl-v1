# FPL Tokvam Multi-GW Optimizer

Replicates Mikel Tokvam's FPL optimization model: rolling-horizon transfer/chip planning, live FPL API and projections, MILP.

## Setup

1. Clone repo  
   `git clone https://github.com/YOUR_USERNAME/fpl_tokvam_multi.git`
2. Install requirements  
   `pip install -r requirements.txt`
3. Run web app  
   `streamlit run app.py`

## Features
- Multi-GW planning (rolling transfer/chip logic)
- Use live FPL data or upload projection CSV
- Squad/bench/captain/EV for each GW, transfer hits, chip simulation
- Modifiable for any horizon/chip rules
