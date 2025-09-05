import streamlit as st
import pandas as pd
import requests

response = requests.get("https://zevent.fr/api/")
data = response.json()
live = data.get("live", [])

df = pd.DataFrame([
    {
        "display": item.get("display"),
        "viewersAmount": item.get("viewersAmount", {}).get("number", 0),
        "donationAmount": item.get("donationAmount", {}).get("number", 0)
    }
    for item in live
])

st.dataframe(
    df,
    column_config={
        "display": st.column_config.TextColumn(
            "Streamer",
        )
        "viewersAmount": st.column_config.NumberColumn(
            "Viewers",
            format="localized",
        ),
        "donationAmount": st.column_config.NumberColumn(
            "Donations (€)",
            format="euro",
        ),
    },
    use_container_width=True
)
