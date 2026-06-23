# streamlit_app.py
# -------------------------------------------------------------
# MLB Position Player Comparator (Improved UI Version)
# -------------------------------------------------------------

import math
import requests
import pandas as pd
import streamlit as st

MLB_API = "https://statsapi.mlb.com/api/v1"
SPORT_ID = 1

# ------------------------------
# Page Config + Styling
# ------------------------------
st.set_page_config(
    page_title="MLB Player Comparator",
    page_icon="⚾",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}

h1, h2, h3 {
    color: #ffffff;
}

div[data-testid="stSelectbox"] {
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------
# Title
# ------------------------------
st.title("⚾ MLB Player Comparator")
st.caption("Compare MLB position players using real-time stats from the MLB Stats API")

# ------------------------------
# Helpers
# ------------------------------
@st.cache_data(ttl=60 * 60)
def fetch_json(url: str, params: dict | None = None):
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

@st.cache_data(ttl=12 * 60 * 60)
def get_teams():
    data = fetch_json(
        f"{MLB_API}/teams",
        params={"sportId": SPORT_ID, "activeStatus": "Y"}
    )
    teams = [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "abbrev": t.get("abbreviation"),
        }
        for t in data.get("teams", [])
    ]
    return pd.DataFrame(teams).sort_values("name")

@st.cache_data(ttl=60 * 60)
def get_team_roster(team_id: int):
    data = fetch_json(f"{MLB_API}/teams/{team_id}/roster", params={"rosterType": "active"})
    roster = []
    for r in data.get("roster", []):
        p = r.get("person", {})
        pos = r.get("position", {})
        roster.append({
            "personId": p.get("id"),
            "fullName": p.get("fullName"),
            "position": pos.get("abbreviation"),
        })
    return pd.DataFrame(roster)

@st.cache_data(ttl=30 * 60)
def get_player_stats(person_id: int, season: int):
    url = f"{MLB_API}/people/{person_id}/stats"
    params = {"stats": "season", "group": "hitting", "season": season}
    data = fetch_json(url, params=params)
    splits = data.get("stats", [{}])[0].get("splits", [])
    if not splits:
        return {}
    return splits[0].get("stat", {})

def safe(val):
    try:
        return float(val)
    except:
        return math.nan

# ------------------------------
# Sidebar Controls
# ------------------------------
teams_df = get_teams()
team_map = dict(zip(teams_df["name"], teams_df["id"]))

with st.sidebar:
    st.header("Controls")

    team_a = st.selectbox("Team A", teams_df["name"])
    team_b = st.selectbox("Team B", teams_df["name"], index=1)

    position = st.selectbox(
        "Position",
        ["C","1B","2B","3B","SS","LF","CF","RF","DH"],
        index=4
    )

    comparison_mode = st.radio(
        "Comparison Mode",
        ["Same Season", "Different Seasons"]
    )

    season = st.number_input(
        "Season",
        min_value=2015,
        max_value=2026,
        value=2026
    )

# ------------------------------
# Season Logic
# ------------------------------
season_a = season
season_b = season

if comparison_mode == "Different Seasons":
    col_a, col_b = st.columns(2)

    with col_a:
        season_a = st.number_input(
            "Season for Player A",
            min_value=2015,
            max_value=2026,
            value=2026,
            key="season_a"
        )

    with col_b:
        season_b = st.number_input(
            "Season for Player B",
            min_value=2015,
            max_value=2026,
            value=2025,
            key="season_b"
        )

# ------------------------------
# Load Data
# ------------------------------
team_a_id = team_map[team_a]
team_b_id = team_map[team_b]

roster_a = get_team_roster(team_a_id)
roster_b = get_team_roster(team_b_id)

players_a = roster_a[roster_a["position"] == position]
players_b = roster_b[roster_b["position"] == position]

# ------------------------------
# Player Selection
# ------------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("## Team A")
    if players_a.empty:
        st.warning("No players found")
        st.stop()

    a_map = dict(zip(players_a["fullName"], players_a["personId"]))
    player_a = st.selectbox("Player A", list(a_map.keys()))
    player_a_id = a_map[player_a]

    st.image(
        f"https://img.mlbstatic.com/mlb-photos/image/upload/w_200,q_auto:best/v1/people/{player_a_id}/headshot/67/current.jpg",
        width=140
    )
    st.markdown(f"**{player_a}**")
    st.caption(team_a)

with col2:
    st.markdown("## Team B")
    if players_b.empty:
        st.warning("No players found")
        st.stop()

    b_map = dict(zip(players_b["fullName"], players_b["personId"]))
    player_b = st.selectbox("Player B", list(b_map.keys()))
    player_b_id = b_map[player_b]

    st.image(
        f"https://img.mlbstatic.com/mlb-photos/image/upload/w_200,q_auto:best/v1/people/{player_b_id}/headshot/67/current.jpg",
        width=140
    )
    st.markdown(f"**{player_b}**")
    st.caption(team_b)

# ------------------------------
# Stats Comparison
# ------------------------------
st.divider()
st.subheader("Stat Comparison")

stats_a = get_player_stats(player_a_id, season_a)
stats_b = get_player_stats(player_b_id, season_b)

fields = [
    ("gamesPlayed","G"),
    ("hits","H"),
    ("homeRuns","HR"),
    ("rbi","RBI"),
    ("avg","AVG"),
    ("obp","OBP"),
    ("slg","SLG"),
    ("ops","OPS"),
    ("strikeOuts","SO"),
]

for key, label in fields:
    a = safe(stats_a.get(key))
    b = safe(stats_b.get(key))

    colA, colM, colB = st.columns([1,0.2,1])

    with colA:
        st.markdown(f"**{label}:** {stats_a.get(key, '-')}")

    with colM:
        if not math.isnan(a) and not math.isnan(b):
            if a > b:
                st.markdown("🟢")
            elif b > a:
                st.markdown("🟢")
            else:
                st.markdown("⚪")
        else:
            st.markdown("-")

    with colB:
        st.markdown(f"**{label}:** {stats_b.get(key, '-')}")
