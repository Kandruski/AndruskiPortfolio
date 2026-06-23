import streamlit as st
import pandas as pd
import numpy as np
import statsapi
import matplotlib.pyplot as plt

st.set_page_config(page_title="MLB Pro Comparator", layout="wide")

# -----------------------------
# PLAYER LOOKUP
# -----------------------------

@st.cache_data
def get_player_id(name):
    try:
        results = statsapi.lookup_player(name)
        if not results:
            return None, None

        player = results[0]
        return player["id"], player["fullName"]
    except:
        return None, None


# -----------------------------
# STATS FETCH (BATTERS)
# -----------------------------

@st.cache_data
def get_batting_stats(player_id, season):
    try:
        data = statsapi.get("person_stats", {
            "personId": player_id,
            "group": "hitting",
            "season": season
        })

        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None

        return splits[0]["stat"]
    except:
        return None


# -----------------------------
# STATS FETCH (PITCHERS)
# -----------------------------

@st.cache_data
def get_pitching_stats(player_id, season):
    try:
        data = statsapi.get("person_stats", {
            "personId": player_id,
            "group": "pitching",
            "season": season
        })

        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None

        return splits[0]["stat"]
    except:
        return None


# -----------------------------
# HEADSHOT
# -----------------------------

def get_headshot(player_id):
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_100,h_100,c_fill,q_auto/v1/people/{player_id}/headshot/67/current"


def safe(val):
    try:
        return float(val)
    except:
        return 0


def colorize(v1, v2):
    if v1 > v2:
        return "🟢", "🔴"
    elif v2 > v1:
        return "🔴", "🟢"
    return "🟡", "🟡"


# -----------------------------
# UI
# -----------------------------

st.title("⚾ MLB Pro Player Comparator")

col1, col2 = st.columns(2)

with col1:
    player1 = st.text_input("Player 1 (First Last)")
    season1 = st.selectbox("Player 1 Season", list(range(2015, 2026)), index=9)

with col2:
    player2 = st.text_input("Player 2 (First Last)")
    season2 = st.selectbox("Player 2 Season", list(range(2015, 2026)), index=9)

mode = st.radio("Mode", ["Batting", "Pitching"])

run = st.button("Compare Players")

# -----------------------------
# MAIN LOGIC
# -----------------------------

if run:

    if not player1 or not player2:
        st.warning("Enter both player names.")
        st.stop()

    p1_id, p1_name = get_player_id(player1)
    p2_id, p2_name = get_player_id(player2)

    if not p1_id or not p2_id:
        st.error("Could not find one or both players.")
        st.stop()

    if mode == "Batting":
        p1_stats = get_batting_stats(p1_id, season1)
        p2_stats = get_batting_stats(p2_id, season2)

        stats_list = ["avg", "homeRuns", "runs", "rbi", "stolenBases", "obp", "slg", "ops"]

    else:
        p1_stats = get_pitching_stats(p1_id, season1)
        p2_stats = get_pitching_stats(p2_id, season2)

        stats_list = ["era", "wins", "strikeOuts", "whip", "inningsPitched"]

    if not p1_stats or not p2_stats:
        st.error("Stats not available for one or both players in selected seasons.")
        st.stop()

    st.divider()

    # -----------------------------
    # PLAYER HEADER
    # -----------------------------

    c1, c2 = st.columns(2)

    with c1:
        st.subheader(f"{p1_name} ({season1})")
        st.image(get_headshot(p1_id), width=80)

    with c2:
        st.subheader(f"{p2_name} ({season2})")
        st.image(get_headshot(p2_id), width=80)

    # -----------------------------
    # TABLE COMPARISON
    # -----------------------------

    rows = []

    for stat in stats_list:
        v1 = safe(p1_stats.get(stat, 0))
        v2 = safe(p2_stats.get(stat, 0))

        icon1, icon2 = colorize(v1, v2)

        rows.append([
            stat,
            f"{icon1} {v1}",
            f"{icon2} {v2}"
        ])

    df = pd.DataFrame(rows, columns=["Stat", p1_name, p2_name])

    st.subheader("📊 Comparison Table")
    st.dataframe(df, use_container_width=True)

    # -----------------------------
    # WIN SUMMARY
    # -----------------------------

    p1_wins = 0
    p2_wins = 0

    for stat in stats_list:
        v1 = safe(p1_stats.get(stat, 0))
        v2 = safe(p2_stats.get(stat, 0))

        if v1 > v2:
            p1_wins += 1
        elif v2 > v1:
            p2_wins += 1

    st.subheader("🏆 Overall Edge")

    st.write(f"**{p1_name}:** {p1_wins}")
    st.write(f"**{p2_name}:** {p2_wins}")

    if p1_wins > p2_wins:
        st.success(f"{p1_name} has the advantage")
    elif p2_wins > p1_wins:
        st.success(f"{p2_name} has the advantage")
    else:
        st.info("Even matchup")
