# streamlit_app.py
# -------------------------------------------------------------
# MLB Position Player Comparator (Streamlit)
# -------------------------------------------------------------
# Features
# - Pick two MLB teams and a position (e.g., SS, CF, 1B, etc.)
# - Choose the specific player from each team who plays that position
# - Fetch season batting stats from MLB Stats API (unofficial)
# - Show headshots, names, teams, and side‑by‑side stat table
# - Automatically highlight the better value per stat in green
#
# How to run locally:
#   1) pip install streamlit requests pandas
#   2) streamlit run streamlit_app.py
#
# Notes:
# - Data source: https://statsapi.mlb.com/ (no API key required)
# - This app focuses on **position players** (non‑pitchers) and hitting stats.
# - If a team has multiple players at a position, you can pick which to compare.

import math
import time
import requests
import pandas as pd
import streamlit as st

MLB_API = "https://statsapi.mlb.com/api/v1"
SPORT_ID = 1  # MLB

# ------------------------------
# Helpers for MLB Stats API
# ------------------------------
@st.cache_data(ttl=60 * 60)
def fetch_json(url: str, params: dict | None = None):
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

@st.cache_data(ttl=12 * 60 * 60)
def get_teams():
    """Return active MLB teams as DataFrame with id, name, and abbreviation."""
    data = fetch_json(
        f"{MLB_API}/teams",
        params={"sportId": SPORT_ID, "activeStatus": "Y"},
    )
    teams = [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "abbrev": t.get("abbreviation"),
        }
        for t in data.get("teams", [])
        if t.get("sport", {}).get("id") == SPORT_ID
    ]
    df = pd.DataFrame(teams).sort_values("name").reset_index(drop=True)
    return df

@st.cache_data(ttl=60 * 60)
def get_team_roster(team_id: int):
    data = fetch_json(f"{MLB_API}/teams/{team_id}/roster", params={"rosterType": "active"})
    roster = []
    for r in data.get("roster", []):
        p = r.get("person", {})
        pos = r.get("position", {})
        roster.append(
            {
                "personId": p.get("id"),
                "fullName": p.get("fullName"),
                "position": pos.get("abbreviation"),
                "primary": r.get("isActive", True),
            }
        )
    return pd.DataFrame(roster)

@st.cache_data(ttl=60 * 60)
def get_team_logo_url(team_id: int) -> str:
    # MLB serves SVG logos at this stable path
    return f"https://www.mlbstatic.com/team-logos/{team_id}.svg"

@st.cache_data(ttl=24 * 60 * 60)
def get_player_headshot_url(person_id: int, size: int = 256) -> str:
    # Headshot service path; size parameter is advisory (server may resize)
    # Fallback image handling is done by Streamlit if URL fails
    return (
        f"https://img.mlbstatic.com/mlb-photos/image/upload/"
        f"w_{size},q_auto:best/v1/people/{person_id}/headshot/67/current.jpg"
    )

@st.cache_data(ttl=30 * 60)
def get_player_hitting_stats(person_id: int, season: int):
    """Return a flat dict of hitting stats for a given player and season."""
    url = f"{MLB_API}/people/{person_id}/stats"
    params = {"stats": "season", "group": "hitting", "season": season}
    data = fetch_json(url, params=params)
    splits = (
        data.get("stats", [{}])[0]
        .get("splits", [])
    )
    if not splits:
        return {}
    # Usually one season split
    stat = splits[0].get("stat", {})
    return stat

# ------------------------------
# UI helpers
# ------------------------------
def numeric(value):
    try:
        if value is None or value == "":
            return math.nan
        return float(value)
    except Exception:
        return math.nan

STAT_FIELDS = [
    ("gamesPlayed", "G"),
    ("plateAppearances", "PA"),
    ("atBats", "AB"),
    ("runs", "R"),
    ("hits", "H"),
    ("doubles", "2B"),
    ("triples", "3B"),
    ("homeRuns", "HR"),
    ("rbi", "RBI"),
    ("stolenBases", "SB"),
    ("caughtStealing", "CS"),
    ("baseOnBalls", "BB"),
    ("strikeOuts", "SO"),
    ("avg", "AVG"),
    ("obp", "OBP"),
    ("slg", "SLG"),
    ("ops", "OPS"),
    ("babip", "BABIP"),
]

# Metrics where LOWER is typically better for hitters
LOWER_IS_BETTER = {"strikeOuts", "caughtStealing"}

POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]

# ------------------------------
# Streamlit App
# ------------------------------
st.set_page_config(page_title="MLB Position Player Comparator", page_icon="⚾", layout="wide")
st.title("⚾ MLB Position Player Comparator")
st.caption("Compare two position players by team, position, and season. Data: MLB Stats API.")

with st.sidebar:
    st.header("Controls")
    season_default = time.gmtime().tm_year  # current year (UTC)

    teams_df = get_teams()
    team_name_to_id = dict(zip(teams_df["name"], teams_df["id"]))

    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        team_a_name = st.selectbox("Team A", teams_df["name"].tolist(), index=0)
    with col_sb2:
        team_b_name = st.selectbox("Team B", teams_df["name"].tolist(), index=1)

    position = st.selectbox("Position", POSITIONS, index=4)  # default SS
    season = st.number_input("Season", min_value=2015, max_value=season_default, value=season_default, step=1)
    st.divider()

# Load rosters for the selected teams
team_a_id = team_name_to_id[team_a_name]
team_b_id = team_name_to_id[team_b_name]

roster_a = get_team_roster(team_a_id)
roster_b = get_team_roster(team_b_id)

# Limit to position players (exclude pitchers) and chosen position
players_a = roster_a[roster_a["position"].eq(position)] if not roster_a.empty else pd.DataFrame()
players_b = roster_b[roster_b["position"].eq(position)] if not roster_b.empty else pd.DataFrame()

col_top_a, col_top_mid, col_top_b = st.columns([1, 0.2, 1])

with col_top_a:
    st.subheader(f"{team_a_name} — {position}")
    if players_a.empty:
        st.warning("No active roster players found at this position.")
        player_a_id = None
        player_a_name = "—"
    else:
        options_a = players_a.set_index("fullName")["personId"].to_dict()
        player_a_name = st.selectbox("Player A", list(options_a.keys()))
        player_a_id = options_a[player_a_name]
        st.image(get_player_headshot_url(player_a_id), width=160)
        st.markdown(f"**{player_a_name}**")
        st.markdown(f"Team: {team_a_name}")

with col_top_b:
    st.subheader(f"{team_b_name} — {position}")
    if players_b.empty:
        st.warning("No active roster players found at this position.")
        player_b_id = None
        player_b_name = "—"
    else:
        options_b = players_b.set_index("fullName")["personId"].to_dict()
        player_b_name = st.selectbox("Player B", list(options_b.keys()))
        player_b_id = options_b[player_b_name]
        st.image(get_player_headshot_url(player_b_id), width=160)
        st.markdown(f"**{player_b_name}**")
        st.markdown(f"Team: {team_b_name}")

st.divider()

# Guard: need two valid players
if not player_a_id or not player_b_id:
    st.info("Select valid players on both teams to see the comparison table.")
    st.stop()

# Fetch stats
with st.spinner("Fetching player stats..."):
    stats_a = get_player_hitting_stats(int(player_a_id), int(season))
    stats_b = get_player_hitting_stats(int(player_b_id), int(season))

if not stats_a and not stats_b:
    st.error("No hitting stats available for the selected season.")
    st.stop()

# Build comparison table
rows = []
for key, label in STAT_FIELDS:
    a_val_raw = stats_a.get(key)
    b_val_raw = stats_b.get(key)
    # Keep display strings for rate stats (.AVG, OBP, SLG, OPS) as-is; others numeric
    a_val = numeric(a_val_raw)
    b_val = numeric(b_val_raw)
    rows.append({"Stat": label, "Player A": a_val, "Player B": b_val})

comp_df = pd.DataFrame(rows)

# Styling function: highlight better value in green; handle lower-is-better cases
def highlight_better(row: pd.Series):
    stat = row["Stat"]
    a = row["Player A"]
    b = row["Player B"]
    # Map back to API key to check LOWER_IS_BETTER
    key_lookup = {lab: key for key, lab in STAT_FIELDS}
    api_key = key_lookup.get(stat)
    lower_better = api_key in LOWER_IS_BETTER

    styles = ["" for _ in row]
    # Indices: 0=Stat, 1=Player A, 2=Player B
    if pd.isna(a) and pd.isna(b):
        return ["", "", ""]
    if pd.isna(a):
        styles[2] = "background-color: #d1fadf"  # B wins (A missing)
        return styles
    if pd.isna(b):
        styles[1] = "background-color: #d1fadf"  # A wins (B missing)
        return styles

    if lower_better:
        if a < b:
            styles[1] = "background-color: #d1fadf"
        elif b < a:
            styles[2] = "background-color: #d1fadf"
    else:
        if a > b:
            styles[1] = "background-color: #d1fadf"
        elif b > a:
            styles[2] = "background-color: #d1fadf"
    return styles

styled = comp_df.style.apply(highlight_better, axis=1)

# Display side-by-side summary header with team logos
header_col1, header_col2, header_col3 = st.columns([1.4, 0.2, 1.4])
with header_col1:
    st.image(get_team_logo_url(team_a_id), width=80)
    st.markdown(f"**{player_a_name}** — *{team_a_name}*")
with header_col3:
    st.image(get_team_logo_url(team_b_id), width=80)
    st.markdown(f"**{player_b_name}** — *{team_b_name}*")

st.dataframe(styled, use_container_width=True)

st.caption(
    "Green cells indicate the better value per row. For some stats (like SO, CS), lower is better."
)

# Extra: compact raw stat JSON (for debugging)
with st.expander("Show raw API values (debug)"):
    st.json({
        player_a_name: stats_a,
        player_b_name: stats_b,
    })
