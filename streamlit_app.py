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

sort_by = st.selectbox(
    "Trier par",
    options=["viewersAmount", "donationAmount"],
    format_func=lambda x: "Viewers" if x == "viewersAmount" else "Donations (€)"
)

df_sorted = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
df_sorted["position"] = df_sorted.index + 1

st.dataframe(
    df_sorted,
    column_config={
        "position": st.column_config.NumberColumn(
            "Position",
            format="d",
        ),
        "display": st.column_config.TextColumn(
            "Streamer",
        ),
        "viewersAmount": st.column_config.NumberColumn(
            "Viewers",
            format="localized",
        ),
        "donationAmount": st.column_config.NumberColumn(
            "Donations (€)",
            format="euro",
        ),
    },
    hide_index=True,
    use_container_width=True
)
