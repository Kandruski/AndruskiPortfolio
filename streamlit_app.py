# streamlit_app.py
# -------------------------------------------------------------
# MLB Position Player Comparator (STABLE + FIXED)
# -------------------------------------------------------------

import math
import requests
import pandas as pd
import streamlit as st

MLB_API = "https://statsapi.mlb.com/api/v1"
SPORT_ID = 1


# ------------------------------
# SAFE REQUEST WRAPPER
# ------------------------------
def fetch_json(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except:
        return {}


# ------------------------------
# TEAMS
# ------------------------------
@st.cache_data(ttl=60 * 60 * 12)
def get_teams():
    data = fetch_json(
        f"{MLB_API}/teams",
        params={"sportId": SPORT_ID, "activeStatus": "Y"},
    )

    teams = []
    for t in data.get("teams", []):
        teams.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "abbrev": t.get("abbreviation"),
        })

    df = pd.DataFrame(teams)
    if not df.empty:
        df = df.sort_values("name").reset_index(drop=True)
    return df


# ------------------------------
# ROSTER
# ------------------------------
@st.cache_data(ttl=60 * 60 * 6)
def get_team_roster(team_id):
    data = fetch_json(
        f"{MLB_API}/teams/{team_id}/roster",
        params={"rosterType": "active"},
    )

    roster = []
    for r in data.get("roster", []):
        p = r.get("person", {})
        pos = r.get("position", {})

        roster.append({
            "personId": p.get("id"),
            "fullName": p.get("fullName"),
            "position": pos.get("abbreviation", ""),
        })

    return pd.DataFrame(roster)


# ------------------------------
# HEADSHOT
# ------------------------------
def headshot(pid):
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_160,h_160,c_fill,q_auto/v1/people/{pid}/headshot/67/current"


# ------------------------------
# PLAYER STATS
# ------------------------------
@st.cache_data(ttl=60 * 60)
def get_player_hitting_stats(person_id, season):
    url = f"{MLB_API}/people/{person_id}/stats"
    params = {"stats": "season", "group": "hitting", "season": season}

    data = fetch_json(url, params=params)

    try:
        stats_block = data.get("stats", [])
        if not stats_block:
            return {}

        splits = stats_block[0].get("splits", [])
        if not splits:
            return {}

        return splits[0].get("stat", {}) or {}
    except:
        return {}


# ------------------------------
# UTIL
# ------------------------------
def safe(v):
    try:
        return float(v)
    except:
        return 0.0


STAT_FIELDS = [
    ("avg", "AVG"),
    ("obp", "OBP"),
    ("slg", "SLG"),
    ("ops", "OPS"),
    ("homeRuns", "HR"),
    ("rbi", "RBI"),
    ("runs", "R"),
    ("hits", "H"),
    ("stolenBases", "SB"),
    ("strikeOuts", "SO"),
]

LOWER_IS_BETTER = {"strikeOuts"}

POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]


# ------------------------------
# APP SETUP
# ------------------------------
st.set_page_config(page_title="MLB Comparator", layout="wide")

st.title("⚾ MLB Position Player Comparator")
st.caption("Stable Streamlit Cloud version (no statsapi / no breaking dependencies)")


# ------------------------------
# SIDEBAR
# ------------------------------
teams_df = get_teams()

if teams_df.empty:
    st.error("Failed to load teams from MLB API.")
    st.stop()

team_map = dict(zip(teams_df["name"], teams_df["id"]))

with st.sidebar:
    st.header("Controls")

    team_a = st.selectbox("Team A", teams_df["name"])
    team_b = st.selectbox("Team B", teams_df["name"], index=1 if len(teams_df) > 1 else 0)

    position = st.selectbox("Position", POSITIONS, index=4)

    season = st.number_input("Season", min_value=2015, max_value=2026, value=2024)


# ------------------------------
# LOAD DATA
# ------------------------------
team_a_id = team_map[team_a]
team_b_id = team_map[team_b]

roster_a = get_team_roster(team_a_id)
roster_b = get_team_roster(team_b_id)

players_a = roster_a[roster_a["position"] == position] if not roster_a.empty else pd.DataFrame()
players_b = roster_b[roster_b["position"] == position] if not roster_b.empty else pd.DataFrame()


# ------------------------------
# PLAYER SELECT
# ------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"{team_a} — {position}")

    if players_a.empty:
        st.warning("No players found.")
        p1_id = None
        p1_name = None
    else:
        options_a = dict(zip(players_a["fullName"], players_a["personId"]))

        p1_name = st.selectbox("Player A", list(options_a.keys()))
        p1_id = options_a.get(p1_name)

        if p1_id:
            st.image(headshot(p1_id), width=120)

with col2:
    st.subheader(f"{team_b} — {position}")

    if players_b.empty:
        st.warning("No players found.")
        p2_id = None
        p2_name = None
    else:
        options_b = dict(zip(players_b["fullName"], players_b["personId"]))

        p2_name = st.selectbox("Player B", list(options_b.keys()))
        p2_id = options_b.get(p2_name)

        if p2_id:
            st.image(headshot(p2_id), width=120)


st.divider()


# ------------------------------
# STOP IF INVALID
# ------------------------------
if not players_a.empty and not players_b.empty and p1_id and p2_id:

    stats_a = get_player_hitting_stats(p1_id, season)
    stats_b = get_player_hitting_stats(p2_id, season)

    if not stats_a or not stats_b:
        st.error("No stats available for this season.")
        st.stop()

    rows = []

    for key, label in STAT_FIELDS:
        a = safe(stats_a.get(key))
        b = safe(stats_b.get(key))

        if key in LOWER_IS_BETTER:
            if a < b:
                ha, hb = "🟢", "🔴"
            elif b < a:
                ha, hb = "🔴", "🟢"
            else:
                ha = hb = "🟡"
        else:
            if a > b:
                ha, hb = "🟢", "🔴"
            elif b > a:
                ha, hb = "🔴", "🟢"
            else:
                ha = hb = "🟡"

        rows.append([label, f"{ha} {a}", f"{hb} {b}"])

    df = pd.DataFrame(rows, columns=["Stat", p1_name, p2_name])

    st.subheader("📊 Comparison")
    st.dataframe(df, use_container_width=True)

    # --------------------------
    # WIN COUNT
    # --------------------------
    p1_wins = 0
    p2_wins = 0

    for key, _ in STAT_FIELDS:
        a = safe(stats_a.get(key))
        b = safe(stats_b.get(key))

        if key in LOWER_IS_BETTER:
            if a < b:
                p1_wins += 1
            elif b < a:
                p2_wins += 1
        else:
            if a > b:
                p1_wins += 1
            elif b > a:
                p2_wins += 1

    st.subheader("🏆 Edge")

    st.write(f"{p1_name}: {p1_wins}")
    st.write(f"{p2_name}: {p2_wins}")

    if p1_wins > p2_wins:
        st.success(f"{p1_name} leads overall")
    elif p2_wins > p1_wins:
        st.success(f"{p2_name} leads overall")
    else:
        st.info("Even matchup")
