from datetime import datetime

import pandas as pd
import requests
import streamlit as st


def fetch_data():
    try:
        response = requests.get("https://zevent.fr/api/", timeout=10)
        response.raise_for_status()
        data = response.json()
        st.session_state["updated_at"] = datetime.now()
        return data
    except requests.RequestException:
        st.error("Impossible de récupérer les données du ZEvent.")
        st.stop()
    except ValueError:
        st.error("L'API du ZEvent a renvoyé des données invalides.")
        st.stop()


data = fetch_data() if "live" not in st.session_state else None

st.title("ZEVENT 2026 light stats")
st.caption(
    f"Dernière mise à jour : {st.session_state['updated_at']:%d/%m/%Y à %H:%M:%S}"
)

if st.button("Rafraîchir les données"):
    data = fetch_data()
    st.session_state["live"] = data["live"]
    st.session_state["globalDonationUrl"] = data["globalDonationUrl"]
    st.session_state["donationAmount"] = data["donationAmount"]
    st.session_state["viewersCount"] = data["viewersCount"]
elif "live" not in st.session_state:
    st.session_state["live"] = data["live"]
    st.session_state["globalDonationUrl"] = data["globalDonationUrl"]
    st.session_state["donationAmount"] = data["donationAmount"]
    st.session_state["viewersCount"] = data["viewersCount"]

live = st.session_state["live"]

en_ligne = sum(item.get("online", False) for item in live)
hors_ligne = len(live) - en_ligne

col1, col2, col3 = st.columns(3)
col1.metric(
    "Viewers totaux", st.session_state["viewersCount"]["formatted"], border=True
)
col2.metric(
    "Dons totaux (€)", st.session_state["donationAmount"]["formatted"], border=True
)
col3.metric(
    "Streamers totaux",
    len(live),
    help=f"🟢 En ligne : {en_ligne} 🔴 Hors ligne : {hors_ligne}",
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

df_sorted = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
df_sorted["position"] = df_sorted.index + 1
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
        "position": st.column_config.NumberColumn("Position"),
        "avatar": st.column_config.ImageColumn("Avatar"),
        "display": st.column_config.TextColumn("Streamer"),
        "twitchUrl": st.column_config.LinkColumn("Twitch", display_text="Twitch"),
        "online": st.column_config.TextColumn("En ligne"),
        "game": st.column_config.TextColumn("Jeu"),
        "viewersAmount": st.column_config.NumberColumn("Viewers", format="localized"),
        "donationAmount": st.column_config.NumberColumn("Donations (€)", format="euro"),
        "donationUrl": st.column_config.LinkColumn("Don", display_text="Don"),
    },
    hide_index=True,
    use_container_width=True,
)

st.markdown(f"[Faire un don global]({st.session_state['globalDonationUrl']})")

st.markdown("---")
st.markdown("🟢 [stats.zevent.fr - Statistiques](https://stats.zevent.fr/)")
st.markdown("🟢 [zevent-stats.louis-julien.dev - ZEvent stats](https://zevent-stats.louis-julien.dev/)")
st.markdown("🔴 [zevent.gdoc.fr - Statistiques](https://zevent.gdoc.fr/statistics)")
st.markdown("🔴 [astucesweb.fr - ZEVENT](https://astucesweb.fr/projets/zevent/)")
