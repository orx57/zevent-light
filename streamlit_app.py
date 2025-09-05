import pandas as pd
import requests
import streamlit as st


def fetch_data():
    response = requests.get("https://zevent.fr/api/")
    data = response.json()
    return data


data = fetch_data() if "live" not in st.session_state else None

st.title("ZEVENT 2025 light stats")

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

# Affichage des totaux globaux
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
            "twitch": item.get("twitch"),
            "online": "🟢" if item.get("online") else "🔴",
            "game": item.get("game"),
            "viewersAmount": item.get("viewersAmount", {}).get("number", 0),
            "donationAmount": item.get("donationAmount", {}).get("number", 0),
            "twitchUrl": f"https://twitch.tv/{item.get('twitch')}",
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

st.dataframe(
    df_sorted,
    column_config={
        "position": st.column_config.NumberColumn("Position"),
        "avatar": st.column_config.ImageColumn("Avatar"),
        "display": st.column_config.TextColumn("Streamer"),
        "online": st.column_config.TextColumn("En ligne"),
        "game": st.column_config.TextColumn("Jeu"),
        "viewersAmount": st.column_config.NumberColumn("Viewers", format="localized"),
        "donationAmount": st.column_config.NumberColumn("Donations (€)", format="euro"),
        "twitchUrl": st.column_config.LinkColumn("Twitch", display_text="Twitch"),
        "donationUrl": st.column_config.LinkColumn("Don", display_text="Don"),
    },
    hide_index=True,
    use_container_width=True,
)

st.markdown(f"[Faire un don global]({st.session_state['globalDonationUrl']})")
