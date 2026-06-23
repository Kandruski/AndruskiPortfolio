import streamlit as st
import pandas as pd
from pybaseball import playerid_lookup, batting_stats
import requests

st.set_page_config(page_title="MLB Player Comparator", layout="wide")

# ---------------------------
# Helpers
# ---------------------------

@st.cache_data
def get_player_id(full_name):
    try:
        parts = full_name.strip().lower().split()

        if len(parts) < 2:
            return None, None

        last = parts[-1]
        first = parts[0]

        df = playerid_lookup(last, first)

        if df.empty:
            return None, None

        mlbam_id = df.iloc[0]["key_mlbam"]
        full_name = f"{df.iloc[0]['name_first']} {df.iloc[0]['name_last']}"

        return mlbam_id, full_name

    except Exception:
        return None, None


@st.cache_data
def get_stats(player_id, season):
    try:
        df = batting_stats(season)
        player_row = df[df["IDfg"] == player_id]
        if player_row.empty:
            return None
        return player_row.iloc[0]
    except Exception:
        return None


def get_headshot(mlbam_id):
    if not mlbam_id:
        return None
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_150,h_150,c_fill,q_auto:best/v1/people/{mlbam_id}/headshot/67/current"


def safe(val):
    return val if val is not None else "N/A"


# ---------------------------
# UI
# ---------------------------

st.title("⚾ MLB Player Comparator")

st.markdown("Compare any two MLB players across any seasons.")

col1, col2 = st.columns(2)

with col1:
    player1_name = st.text_input("Player 1 (First Last)")
    season1 = st.selectbox("Player 1 Season", list(range(2015, 2026)), index=9)

with col2:
    player2_name = st.text_input("Player 2 (First Last)")
    season2 = st.selectbox("Player 2 Season", list(range(2015, 2026)), index=9)

run = st.button("Compare Players")

# ---------------------------
# Logic
# ---------------------------

if run:

    if not player1_name or not player2_name:
        st.warning("Please enter both player names.")
        st.stop()

    p1_id, p1_clean = get_player_id(player1_name)
    p2_id, p2_clean = get_player_id(player2_name)

    if not p1_id or not p2_id:
        st.error("Could not find one or both players. Check spelling.")
        st.stop()

    p1_stats = get_stats(p1_id, season1)
    p2_stats = get_stats(p2_id, season2)

    if p1_stats is None or p2_stats is None:
        st.error("Stats not found for one or both players in selected seasons.")
        st.stop()

    # ---------------------------
    # HEADSHOTS
    # ---------------------------

    c1, c2 = st.columns(2)

    with c1:
        st.subheader(f"{p1_clean} ({season1})")
        st.image(get_headshot(p1_id), width=90)

    with c2:
        st.subheader(f"{p2_clean} ({season2})")
        st.image(get_headshot(p2_id), width=90)

    # ---------------------------
    # STAT COMPARISON
    # ---------------------------

    stats_to_show = [
        "AVG",
        "HR",
        "R",
        "RBI",
        "SB",
        "OBP",
        "SLG",
        "OPS",
        "WAR"
    ]

    comparison = pd.DataFrame({
        "Stat": stats_to_show,
        p1_clean: [safe(p1_stats.get(stat)) for stat in stats_to_show],
        p2_clean: [safe(p2_stats.get(stat)) for stat in stats_to_show],
    })

    st.subheader("📊 Comparison")
    st.dataframe(comparison, use_container_width=True)

    # ---------------------------
    # HIGHLIGHT WINNER STATS
    # ---------------------------

    st.subheader("🏆 Advantage Summary")

    for stat in stats_to_show:
        v1 = p1_stats.get(stat)
        v2 = p2_stats.get(stat)

        try:
            if v1 > v2:
                st.write(f"**{stat}:** {p1_clean} leads")
            elif v2 > v1:
                st.write(f"**{stat}:** {p2_clean} leads")
            else:
                st.write(f"**{stat}:** Tie")
        except:
            st.write(f"**{stat}:** N/A comparison")
