import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

FRENCH_TIMEZONE = ZoneInfo("Europe/Paris")
st.set_page_config(page_title="ZEVENT Stats", page_icon="📊", layout="wide")


@st.fragment(run_every="60s")
def auto_refresh():
    now = time.monotonic()
    last_refresh = st.session_state.get("last_auto_refresh")

    if last_refresh is None:
        st.session_state["last_auto_refresh"] = now
    elif now - last_refresh >= 60:
        st.session_state["last_auto_refresh"] = now
        st.session_state.pop("live", None)
        st.rerun()


auto_refresh()


def fetch_data():
    try:
        response = requests.get("https://zevent.fr/api/", timeout=10)
        response.raise_for_status()
        data = response.json()
        st.session_state["updated_at"] = datetime.now(FRENCH_TIMEZONE)
        return data
    except requests.RequestException:
        st.error("Impossible de récupérer les données du ZEvent.")
        st.stop()
    except ValueError:
        st.error("L'API du ZEvent a renvoyé des données invalides.")
        st.stop()


if "live" not in st.session_state:
    data = fetch_data()
    st.session_state["live"] = data["live"]
    st.session_state["globalDonationUrl"] = data["globalDonationUrl"]
    st.session_state["donationAmount"] = data["donationAmount"]
    st.session_state["viewersCount"] = data["viewersCount"]

header_title, header_actions = st.columns([3, 1], vertical_alignment="center")

with header_title:
    st.title("ZEVENT 2026")
    updated_at = st.session_state.get("updated_at")
    update_label = (
        "Dernière mise à jour : indisponible"
        if updated_at is None
        else f"Dernière mise à jour : {updated_at:%d/%m/%Y à %H:%M:%S}"
    )
    st.caption(f"🟢 Direct · {update_label}")

with header_actions:
    st.link_button(
        "Faire un don global",
        st.session_state["globalDonationUrl"],
        use_container_width=True,
    )

if st.button("Rafraîchir les données"):
    data = fetch_data()
    st.session_state["live"] = data["live"]
    st.session_state["globalDonationUrl"] = data["globalDonationUrl"]
    st.session_state["donationAmount"] = data["donationAmount"]
    st.session_state["viewersCount"] = data["viewersCount"]

live = st.session_state["live"]

en_ligne = sum(item.get("online", False) for item in live)
hors_ligne = len(live) - en_ligne

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Viewers totaux", st.session_state["viewersCount"]["formatted"], border=True
)
col2.metric(
    "Dons totaux (€)", st.session_state["donationAmount"]["formatted"], border=True
)
col3.metric(
    "Streamers en direct",
    en_ligne,
    help=(
        f"{en_ligne / len(live):.0%} des streamers sont en direct."
        if live
        else "Aucun streamer disponible."
    ),
    border=True,
)
col4.metric(
    "Streamers totaux",
    len(live),
    help=f"{en_ligne} en direct · {hors_ligne} hors ligne",
    border=True,
)

df = pd.DataFrame(
    [
        {
            "avatar": item.get("profileUrl"),
            "display": item.get("display"),
            "twitchUrl": f"https://twitch.tv/{item.get('twitch')}",
            "online": "🟢" if item.get("online") else "🔴",
            "game": item.get("game"),
            "viewersAmount": item.get("viewersAmount", {}).get("number", 0),
            "donationAmount": item.get("donationAmount", {}).get("number", 0),
            "donationUrl": item.get("donationUrl"),
        }
        for item in live
    ]
)

sort_by = st.selectbox(
    "Trier par",
    options=["viewersAmount", "donationAmount"],
    format_func=lambda x: "Viewers" if x == "viewersAmount" else "Donations (€)",
)
online_only = st.checkbox("En ligne uniquement")

if online_only:
    df = df[df["online"] == "🟢"]

df_sorted = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
rank_badges = {1: "🥇", 2: "🥈", 3: "🥉"}
df_sorted["position"] = [
    f"{position} {rank_badges[position]}"
    if position in rank_badges
    else str(position)
    for position in range(1, len(df_sorted) + 1)
]
df_sorted = df_sorted[
    ["position"]
    + [
        column
        for column in df_sorted.columns
        if column not in ["position", "twitchUrl"]
    ]
    + ["twitchUrl"]
]

st.dataframe(
    df_sorted,
    column_config={
        "position": st.column_config.TextColumn("Position", width="small"),
        "avatar": st.column_config.ImageColumn("Avatar", width="small"),
        "display": st.column_config.TextColumn("Streamer", width="medium"),
        "twitchUrl": st.column_config.LinkColumn(
            "Chaîne", display_text="Ouvrir", width="small"
        ),
        "online": st.column_config.TextColumn("En ligne", width="small"),
        "game": st.column_config.TextColumn("Jeu", width="medium"),
        "viewersAmount": st.column_config.NumberColumn(
            "Viewers", format="localized", width="small"
        ),
        "donationAmount": st.column_config.NumberColumn(
            "Donations (€)", format="euro", width="small"
        ),
        "donationUrl": st.column_config.LinkColumn(
            "Faire un don", display_text="Don", width="small"
        ),
    },
    hide_index=True,
    use_container_width=True,
)

st.subheader("Classements")
chart_col1, chart_col2 = st.columns(2)

top_viewers = (
    df_sorted.nlargest(10, "viewersAmount")
    .set_index("display")["viewersAmount"]
)
top_donations = (
    df_sorted.nlargest(10, "donationAmount")
    .set_index("display")["donationAmount"]
)

chart_col1.caption("Top 10 viewers")
chart_col1.bar_chart(top_viewers, height=300)
chart_col2.caption("Top 10 dons")
chart_col2.bar_chart(top_donations, height=300)

st.markdown("---")
st.markdown("- [stats.zevent.fr - Statistiques](https://stats.zevent.fr/)")
st.markdown("- [zevent-stats.louis-julien.dev - ZEvent stats](https://zevent-stats.louis-julien.dev/)")
st.markdown("- [zevent.gdoc.fr - Statistiques](https://zevent.gdoc.fr/statistics)")
st.markdown("- [astucesweb.fr - ZEVENT](https://astucesweb.fr/projets/zevent/)")

version_datetime = datetime.now(FRENCH_TIMEZONE)
iso_calendar = version_datetime.isocalendar()
version = (
    f"v{iso_calendar.year}.{iso_calendar.week:02d}."
    f"{iso_calendar.weekday}-{version_datetime:%H%M}"
)
st.caption(version)
