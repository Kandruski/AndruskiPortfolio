import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="MLB Pro Comparator", layout="wide")

# -----------------------------
# MLB API HELPERS (NO LIBRARIES)
# -----------------------------

def lookup_player(name):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/search?names={name}"
        r = requests.get(url).json()

        people = r.get("people", [])
        if not people:
            return None, None

        p = people[0]
        return p["id"], p["fullName"]
    except:
        return None, None


def get_stats(player_id, season, group="hitting"):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&season={season}&group={group}"
        r = requests.get(url).json()

        stats = r.get("stats", [])
        if not stats:
            return None

        splits = stats[0].get("splits", [])
        if not splits:
            return None

        return splits[0]["stat"]
    except:
        return None


def headshot(player_id):
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_100,h_100,c_fill,q_auto/v1/people/{player_id}/headshot/67/current"


def safe(val):
    try:
        return float(val)
    except:
        return 0


# -----------------------------
# UI
# -----------------------------

st.title("⚾ MLB Pro Comparator (Stable Version)")

col1, col2 = st.columns(2)

with col1:
    p1 = st.text_input("Player 1")
    season1 = st.selectbox("Season 1", list(range(2015, 2026)), index=9)

with col2:
    p2 = st.text_input("Player 2")
    season2 = st.selectbox("Season 2", list(range(2015, 2026)), index=9)

mode = st.radio("Mode", ["Batting", "Pitching"])

run = st.button("Compare")

# -----------------------------
# MAIN LOGIC
# -----------------------------

if run:

    if not p1 or not p2:
        st.warning("Enter both players")
        st.stop()

    p1_id, p1_name = lookup_player(p1)
    p2_id, p2_name = lookup_player(p2)

    if not p1_id or not p2_id:
        st.error("Player not found")
        st.stop()

    group = "hitting" if mode == "Batting" else "pitching"

    p1_stats = get_stats(p1_id, season1, group)
    p2_stats = get_stats(p2_id, season2, group)

    if not p1_stats or not p2_stats:
        st.error("Stats not available for selected season")
        st.stop()

    st.divider()

    # -----------------------------
    # HEADER
    # -----------------------------

    c1, c2 = st.columns(2)

    with c1:
        st.subheader(f"{p1_name} ({season1})")
        st.image(headshot(p1_id), width=80)

    with c2:
        st.subheader(f"{p2_name} ({season2})")
        st.image(headshot(p2_id), width=80)

    # -----------------------------
    # STATS
    # -----------------------------

    if mode == "Batting":
        stats_list = ["avg", "homeRuns", "runs", "rbi", "stolenBases", "obp", "slg", "ops"]
    else:
        stats_list = ["era", "wins", "strikeOuts", "whip", "inningsPitched"]

    rows = []

    for s in stats_list:
        v1 = safe(p1_stats.get(s, 0))
        v2 = safe(p2_stats.get(s, 0))

        if v1 > v2:
            r1, r2 = "🟢", "🔴"
        elif v2 > v1:
            r1, r2 = "🔴", "🟢"
        else:
            r1, r2 = "🟡", "🟡"

        rows.append([s, f"{r1} {v1}", f"{r2} {v2}"])

    df = pd.DataFrame(rows, columns=["Stat", p1_name, p2_name])

    st.subheader("📊 Comparison")
    st.dataframe(df, use_container_width=True)

    # -----------------------------
    # WIN SUMMARY
    # -----------------------------

    p1_wins = 0
    p2_wins = 0

    for s in stats_list:
        v1 = safe(p1_stats.get(s, 0))
        v2 = safe(p2_stats.get(s, 0))

        if v1 > v2:
            p1_wins += 1
        elif v2 > v1:
            p2_wins += 1

    st.subheader("🏆 Edge")

    if p1_wins > p2_wins:
        st.success(f"{p1_name} leads ({p1_wins}–{p2_wins})")
    elif p2_wins > p1_wins:
        st.success(f"{p2_name} leads ({p2_wins}–{p1_wins})")
    else:
        st.info("Even matchup")
