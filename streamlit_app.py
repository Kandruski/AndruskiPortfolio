import streamlit as st
import pandas as pd
import numpy as np
from pybaseball import batting_stats, pitching_stats
import matplotlib.pyplot as plt

st.set_page_config(page_title="MLB Pro Comparator", layout="wide")

# -----------------------------
# Load player pools (cached)
# -----------------------------

@st.cache_data
def load_batters(season):
    df = batting_stats(season)
    df["label"] = df["Name"] + " (" + df["Team"].astype(str) + ")"
    return df

@st.cache_data
def load_pitchers(season):
    df = pitching_stats(season)
    df["label"] = df["Name"] + " (" + df["Team"].astype(str) + ")"
    return df


def get_player_row(df, name_label):
    return df[df["label"] == name_label].iloc[0]


# -----------------------------
# UI MODE
# -----------------------------

st.title("⚾ MLB Pro Player Comparator")

mode = st.radio("Mode", ["Batters", "Pitchers"])

season1 = st.selectbox("Player 1 Season", list(range(2015, 2026)), index=9)
season2 = st.selectbox("Player 2 Season", list(range(2015, 2026)), index=9)

# Load correct datasets
if mode == "Batters":
    df1 = load_batters(season1)
    df2 = load_batters(season2)
    stats = ["AVG", "HR", "R", "RBI", "SB", "OBP", "SLG", "OPS", "WAR"]
else:
    df1 = load_pitchers(season1)
    df2 = load_pitchers(season2)
    stats = ["ERA", "W", "SO", "WHIP", "IP", "WAR"]


# -----------------------------
# Player selection (PRO UX)
# -----------------------------

col1, col2 = st.columns(2)

with col1:
    p1 = st.selectbox("Player 1", df1["label"].sort_values().unique())

with col2:
    p2 = st.selectbox("Player 2", df2["label"].sort_values().unique())


run = st.button("Compare Players")


# -----------------------------
# Comparison logic
# -----------------------------

def colorize(v1, v2):
    if v1 > v2:
        return "🟢", "🔴"
    elif v2 > v1:
        return "🔴", "🟢"
    else:
        return "🟡", "🟡"


def safe(val):
    return 0 if pd.isna(val) else val


# -----------------------------
# MAIN OUTPUT
# -----------------------------

if run:

    p1_row = get_player_row(df1, p1)
    p2_row = get_player_row(df2, p2)

    st.divider()

    # -------------------------
    # HEADER SECTION
    # -------------------------

    c1, c2 = st.columns(2)

    with c1:
        st.subheader(f"{p1} ({season1})")
        st.image(
            f"https://img.mlbstatic.com/mlb-photos/image/upload/w_100,h_100,c_fill,q_auto/v1/people/{p1_row['IDfg']}/headshot/67/current",
            width=80
        )

    with c2:
        st.subheader(f"{p2} ({season2})")
        st.image(
            f"https://img.mlbstatic.com/mlb-photos/image/upload/w_100,h_100,c_fill,q_auto/v1/people/{p2_row['IDfg']}/headshot/67/current",
            width=80
        )

    # -------------------------
    # TABLE COMPARISON
    # -------------------------

    rows = []

    for stat in stats:
        v1 = safe(p1_row.get(stat))
        v2 = safe(p2_row.get(stat))

        icon1, icon2 = colorize(v1, v2)

        rows.append([
            stat,
            f"{icon1} {v1}",
            f"{icon2} {v2}"
        ])

    comp_df = pd.DataFrame(rows, columns=["Stat", p1, p2])

    st.subheader("📊 Stat Comparison")
    st.dataframe(comp_df, use_container_width=True)


    # -------------------------
    # WINNER SUMMARY
    # -------------------------

    st.subheader("🏆 Edge Summary")

    p1_wins = 0
    p2_wins = 0

    for stat in stats:
        v1 = safe(p1_row.get(stat))
        v2 = safe(p2_row.get(stat))

        if v1 > v2:
            p1_wins += 1
        elif v2 > v1:
            p2_wins += 1

    st.write(f"**{p1} Wins:** {p1_wins}")
    st.write(f"**{p2} Wins:** {p2_wins}")

    if p1_wins > p2_wins:
        st.success(f"{p1} has the overall edge")
    elif p2_wins > p1_wins:
        st.success(f"{p2} has the overall edge")
    else:
        st.info("Even matchup")


    # -------------------------
    # RADAR CHART
    # -------------------------

    st.subheader("📈 Radar Comparison")

    p1_vals = [safe(p1_row.get(s)) for s in stats]
    p2_vals = [safe(p2_row.get(s)) for s in stats]

    angles = np.linspace(0, 2*np.pi, len(stats), endpoint=False).tolist()
    p1_vals += p1_vals[:1]
    p2_vals += p2_vals[:1]
    angles += angles[:1]

    fig = plt.figure()
    ax = plt.subplot(111, polar=True)

    ax.plot(angles, p1_vals, label=p1)
    ax.fill(angles, p1_vals, alpha=0.1)

    ax.plot(angles, p2_vals, label=p2)
    ax.fill(angles, p2_vals, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(stats)
    ax.legend()

    st.pyplot(fig)
