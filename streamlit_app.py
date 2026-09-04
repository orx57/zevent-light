import time
from datetime import datetime
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import requests
import streamlit as st

FRENCH_TIMEZONE = ZoneInfo("Europe/Paris")
st.set_page_config(page_title="ZEVENT Stats", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
        :root {
            --zevent-ink: #292b38;
            --zevent-muted: #737784;
            --zevent-accent: #e6533c;
            --zevent-surface: #ffffff;
            --zevent-border: #e4e5e9;
        }

        [data-testid="stAppViewContainer"] {
            background: #f7f7f8;
        }

        [data-testid="stMainBlockContainer"] {
            padding-top: 3rem;
            padding-bottom: 3rem;
        }

        h1 {
            color: var(--zevent-ink);
            letter-spacing: 0;
            margin-bottom: 0.25rem;
        }

        [data-testid="stMetric"] {
            background: var(--zevent-surface);
            border: 1px solid var(--zevent-border);
            border-top: 3px solid var(--zevent-accent);
            border-radius: 0.75rem;
            box-shadow: 0 4px 14px rgba(41, 43, 56, 0.05);
            min-height: 7rem;
            padding: 1rem 1.1rem;
        }

        [data-testid="stMetricLabel"] {
            color: var(--zevent-muted);
            font-weight: 600;
        }

        [data-testid="stMetricValue"] {
            color: var(--zevent-ink);
        }

        .live-status {
            align-items: center;
            color: var(--zevent-muted);
            display: flex;
            font-size: 0.85rem;
            gap: 0.45rem;
        }

        .live-status__dot {
            background: #6eb644;
            border-radius: 50%;
            display: inline-block;
            height: 0.55rem;
            width: 0.55rem;
        }

        .live-status__label {
            color: #4f8d2f;
            font-weight: 700;
            letter-spacing: 0.04em;
        }

        .section-heading {
            border-left: 4px solid var(--zevent-accent);
            color: var(--zevent-ink);
            font-size: 1.35rem;
            font-weight: 700;
            margin: 2.25rem 0 0.75rem;
            padding-left: 0.75rem;
        }

        .toolbar-label {
            color: var(--zevent-muted);
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--zevent-border);
            border-radius: 0.75rem;
            box-shadow: 0 4px 14px rgba(41, 43, 56, 0.04);
            overflow: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


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
    st.markdown(
        f'<div class="live-status"><span class="live-status__dot"></span>'
        f'<span class="live-status__label">DIRECT</span><span>· {update_label}</span></div>',
        unsafe_allow_html=True,
    )

with header_actions:
    st.link_button(
        "Faire un don global",
        st.session_state["globalDonationUrl"],
        use_container_width=True,
    )
    if st.button("Rafraîchir les données", use_container_width=True):
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
            "online": "🟢 En ligne" if item.get("online") else "🔴 Hors ligne",
            "game": item.get("game"),
            "viewersAmount": item.get("viewersAmount", {}).get("number", 0),
            "donationAmount": item.get("donationAmount", {}).get("number", 0),
            "donationUrl": item.get("donationUrl"),
        }
        for item in live
    ]
)

st.markdown('<div class="section-heading">Streamers</div>', unsafe_allow_html=True)
with st.container(border=True):
    search_col, sort_col, filter_col = st.columns([2, 1, 1], vertical_alignment="bottom")
    with search_col:
        st.markdown('<div class="toolbar-label">Rechercher</div>', unsafe_allow_html=True)
        search_query = st.text_input(
            "Rechercher",
            placeholder="Streamer ou jeu",
            label_visibility="collapsed",
        )
    with sort_col:
        st.markdown('<div class="toolbar-label">Trier par</div>', unsafe_allow_html=True)
        sort_by = st.selectbox(
            "Trier par",
            options=["viewersAmount", "donationAmount"],
            format_func=lambda x: "Viewers" if x == "viewersAmount" else "Donations (€)",
            label_visibility="collapsed",
        )
    with filter_col:
        st.markdown('<div class="toolbar-label">Afficher</div>', unsafe_allow_html=True)
        view_mode = st.segmented_control(
            "Afficher",
            options=["En direct", "Tous"],
            default="En direct",
            selection_mode="single",
            label_visibility="collapsed",
        )

if search_query:
    search_mask = df["display"].str.contains(search_query, case=False, na=False)
    search_mask |= df["game"].fillna("").str.contains(
        search_query, case=False, na=False
    )
    df = df[search_mask]

if view_mode == "En direct":
    df = df[df["online"] == "🟢 En ligne"]

st.caption(
    f"{len(df)} streamer{'s' if len(df) != 1 else ''} affiché"
    f"{'s' if len(df) != 1 else ''} · "
    f"{en_ligne} en direct au total"
)

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
        "online": st.column_config.TextColumn("Statut", width="small"),
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

st.markdown(
    '<div class="section-heading">Classement des streamers</div>',
    unsafe_allow_html=True,
)
chart_col1, chart_col2 = st.columns(2)

top_viewers = df_sorted.nlargest(10, "viewersAmount")
top_donations = df_sorted.nlargest(10, "donationAmount")

with chart_col1:
    st.caption("Top 10 viewers")
    viewers_chart = (
        alt.Chart(top_viewers)
        .mark_bar(cornerRadiusEnd=4, color="#e6533c")
        .encode(
            x=alt.X("viewersAmount:Q", title="Viewers"),
            y=alt.Y("display:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("display:N", title="Streamer"),
                alt.Tooltip("viewersAmount:Q", title="Viewers", format=",.0f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(viewers_chart, use_container_width=True)

with chart_col2:
    st.caption("Top 10 dons")
    donations_chart = (
        alt.Chart(top_donations)
        .mark_bar(cornerRadiusEnd=4, color="#6f8f3d")
        .encode(
            x=alt.X("donationAmount:Q", title="Dons (€)"),
            y=alt.Y("display:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("display:N", title="Streamer"),
                alt.Tooltip("donationAmount:Q", title="Dons (€)", format=",.2f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(donations_chart, use_container_width=True)

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
