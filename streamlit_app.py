import streamlit as st
import pandas as pd
import requests

# Charger les données depuis l'API
response = requests.get("https://zevent.fr/api/")
data = response.json()

# Supposons que la liste "live" est dans data["live"]
live = data.get("live", [])

# Transformation en DataFrame
df = pd.DataFrame([
    {
        "display": item.get("display"),
        "viewersAmount": item.get("viewersAmount", {}).get("number"),
        "donationAmount": item.get("donationAmount", {}).get("number")
    }
    for item in live
])

# Affichage de la table avec filtrage et tri
st.dataframe(df, use_container_width=True)
