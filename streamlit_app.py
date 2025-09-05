import pandas as pd
import requests
import streamlit as st


def fetch_data():
    response = requests.get("https://zevent.fr/api/")
    data = response.json()
    return data.get("live", [])


if st.button("Rafraîchir les données"):
    st.session_state["live"] = fetch_data()
elif "live" not in st.session_state:
    st.session_state["live"] = fetch_data()

live = st.session_state["live"]

df = pd.DataFrame(
    [
        {
            "display": item.get("display"),
            "viewersAmount": item.get("viewersAmount", {}).get("number", 0),
            "donationAmount": item.get("donationAmount", {}).get("number", 0),
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
        "display": st.column_config.TextColumn("Streamer"),
        "viewersAmount": st.column_config.NumberColumn("Viewers", format="localized"),
        "donationAmount": st.column_config.NumberColumn("Donations (€)", format="euro"),
    },
    hide_index=True,
    use_container_width=True,
)
