import streamlit as st
import pandas as pd
import statsapi

st.set_page_config(page_title="MLB Pro Comparator", layout="wide")

# -----------------------------
# SAFE HELPERS
# -----------------------------

@st.cache_data
def lookup_player(name):
    try:
        results = statsapi.lookup_player(name)
        if not results:
            return None, None

        p = results[0]
        return p["id"], p["fullName"]
    except:
        return None, None


def get_stats(player_id, season, group):
    try:
        data = statsapi.get("person_stats", {
            "personId": player_id,
            "group": group,
            "season": season
        })

        stats_block = data.get("stats", [])
        if not stats_block:
            return None

        splits = stats_block[0].get("splits", [])
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
# UI (NO API CALLS HERE)
# -----------------------------

st.title("⚾ MLB Pro Comparator")

col1, col2 = st.columns(2)

with col1:
    p1_name = st.text_input("Player 1")
    season1 = st.selectbox("Season 1", list(range(2015, 2026)), index=9)

with col2:
    p2_name = st.text_input("Player 2")
    season2 = st.selectbox("Season 2", list(range(2015, 2026)), index=9)

mode = st.radio("Mode", ["Batting", "Pitching"])

run = st.button("Compare")


# -----------------------------
# RUN ONLY AFTER CLICK
# -----------------------------

if run:

    if not p1_name or not p2_name:
        st.warning("Enter both players")
        st.stop()

    p1_id, p1_full = lookup_player(p1_name)
    p2_id, p2_full = lookup_player(p2_name)

    if not p1_id or not p2_id:
        st.error("Player not found")
        st.stop()

    group = "hitting" if mode == "Batting" else "pitching"

    p1_stats = get_stats(p1_id, season1, group)
    p2_stats = get_stats(p2_id, season2, group)

    if not p1_stats or not p2_stats:
        st.error("Stats not available for selected seasons")
        st.stop()

    st.divider()

    # -----------------------------
    # HEADER
    # -----------------------------

    c1, c2 = st.columns(2)

    with c1:
        st.subheader(f"{p1_full} ({season1})")
        st.image(headshot(p1_id), width=80)

    with c2:
        st.subheader(f"{p2_full} ({season2})")
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

    df = pd.DataFrame(rows, columns=["Stat", p1_full, p2_full])

    st.subheader("📊 Comparison")
    st.dataframe(df, use_container_width=True)

    # -----------------------------
    # SUMMARY
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

    st.write(f"{p1_full}: {p1_wins}")
    st.write(f"{p2_full}: {p2_wins}")

    if p1_wins > p2_wins:
        st.success(f"{p1_full} leads overall")
    elif p2_wins > p1_wins:
        st.success(f"{p2_full} leads overall")
    else:
        st.info("Even matchup")
