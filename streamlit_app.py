import requests
import pandas as pd
import streamlit as st

MLB_API = "https://statsapi.mlb.com/api/v1"


# -----------------------------
# SAFE API
# -----------------------------
def fetch_json(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except:
        return {}


# -----------------------------
# GET ALL MLB PLAYERS (SEARCHABLE)
# -----------------------------
@st.cache_data(ttl=60 * 60 * 24)
def get_all_players():
    data = fetch_json(f"{MLB_API}/sports/1/players", params={"season": 2024})

    players = []
    for p in data.get("people", []):
        players.append({
            "id": p.get("id"),
            "name": p.get("fullName"),
            "team": (p.get("currentTeam", {}) or {}).get("name", "FA"),
            "position": p.get("primaryPosition", {}).get("abbreviation", ""),
        })

    df = pd.DataFrame(players)
    return df.sort_values("name")


# -----------------------------
# HEADSHOT (SMALLER FIX)
# -----------------------------
def headshot(pid):
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_120,h_120,c_fill,q_auto/v1/people/{pid}/headshot/67/current"


# -----------------------------
# STATS
# -----------------------------
def get_stats(pid, season):
    data = fetch_json(
        f"{MLB_API}/people/{pid}/stats",
        params={"stats": "season", "group": "hitting", "season": season},
    )

    try:
        splits = data.get("stats", [])[0].get("splits", [])
        if not splits:
            return {}
        return splits[0].get("stat", {}) or {}
    except:
        return {}


# -----------------------------
# UI
# -----------------------------
st.set_page_config(layout="wide")
st.title("⚾ MLB Player Comparator (Pro UI Upgrade)")


players_df = get_all_players()

if players_df.empty:
    st.error("Failed to load players")
    st.stop()


# -----------------------------
# PLAYER SEARCH (NO TEAM LIMIT)
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Player A")

    p1_name = st.selectbox(
        "Search Player A",
        players_df["name"].tolist()
    )

    p1_row = players_df[players_df["name"] == p1_name].iloc[0]

    st.image(headshot(p1_row["id"]), width=90)
    season_a = st.number_input("Season A", 2015, 2026, 2024, key="a")


with col2:
    st.subheader("Player B")

    p2_name = st.selectbox(
        "Search Player B",
        players_df["name"].tolist()
    )

    p2_row = players_df[players_df["name"] == p2_name].iloc[0]

    st.image(headshot(p2_row["id"]), width=90)
    season_b = st.number_input("Season B", 2015, 2026, 2024, key="b")


st.divider()


# -----------------------------
# COMPARE
# -----------------------------
stats_a = get_stats(p1_row["id"], season_a)
stats_b = get_stats(p2_row["id"], season_b)


fields = [
    ("avg", "AVG"),
    ("obp", "OBP"),
    ("slg", "SLG"),
    ("ops", "OPS"),
    ("homeRuns", "HR"),
    ("rbi", "RBI"),
    ("runs", "R"),
    ("hits", "H"),
]


rows = []

for k, label in fields:
    a = stats_a.get(k, 0)
    b = stats_b.get(k, 0)

    try:
        a_f = float(a)
        b_f = float(b)
    except:
        a_f = b_f = 0

    if a_f > b_f:
        a_show = f"🟢 {a}"
        b_show = f"🔴 {b}"
    elif b_f > a_f:
        a_show = f"🔴 {a}"
        b_show = f"🟢 {b}"
    else:
        a_show = b_show = f"🟡 {a}"

    rows.append([label, a_show, b_show])


df = pd.DataFrame(rows, columns=["Stat", p1_name, p2_name])

st.subheader("📊 Comparison")
st.dataframe(df, use_container_width=True)


st.success("Now you can compare ANY player across ANY season (clean UI version)")
