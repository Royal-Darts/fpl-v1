import streamlit as st
from fpl_optimizer import fetch_fpl_data, fetch_projection, rolling_horizon

st.title("FPL Tokvam-Style Multi-GW Optimizer")
n_gw = st.slider("Planning Horizon (Gameweeks)", 1, 6, 3)
budget = st.number_input("Team Budget (£m)", 80.0, 105.0, 100.0)
ft = st.number_input("Free Transfers (for GW1)", 0, 2, 1)
chips = st.multiselect("Available Chips", ["Wildcard", "Bench Boost", "Free Hit", "Triple Captain"])
proj_csv = st.file_uploader("Upload Projection CSV (optional)", type="csv")
players = fetch_fpl_data()
if proj_csv is not None:
    import io
    proj = fetch_projection(io.StringIO(proj_csv.read().decode()), players, n_gw)
else:
    proj = fetch_projection(None, players, n_gw)
start_gw = st.number_input("Start Gameweek", 1, 38, 1)
if st.button("Run Optimization"):
    result = rolling_horizon(proj, start_gw=start_gw, n_gw=n_gw, budget=budget, free_transfers=int(ft), chips=chips)
    for gwres in result:
        st.markdown(f"### GW{gwres['gw']} – Expected Points: {gwres['expected_points']:.2f} (Hits: {gwres['hits']})")
        st.markdown(gwres["squad"].to_markdown())
        st.markdown(f"**Captain:** {gwres['captain']}")
        st.markdown(f"**Bench:** {gwres['bench']}")
