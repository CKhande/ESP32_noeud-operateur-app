# ---------------------------------------------------------
#  DASHBOARD STREAMLIT EN TEMPS RÉEL (MQTT → GAUGES + GRAPH)
# ---------------------------------------------------------

import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
import pandas as pd
from streamlit_echarts import st_echarts

# ---------------------------------------------------------
#  CONFIG STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dashboard ESP32",
    layout="wide"
)

st.title("📡 Dashboard ESP32 - Temps Réel")
st.write("Données reçues depuis MQTT → Broker : 172.161.53.116")


# ---------------------------------------------------------
#  VARIABLES GLOBALES (dernières mesures)
# ---------------------------------------------------------
data = {
    "temperature": 0,
    "humidite": 0,
    "pot": 0,
    "ir": 0
}

# Historique pour les graphes
history = {
    "time": [],
    "temperature": [],
    "humidite": [],
    "pot": [],
    "ir": []
}

# ---------------------------------------------------------
#  CALLBACK MQTT
# ---------------------------------------------------------
def on_message(client, userdata, msg):
    global data, history

    try:
        payload = json.loads(msg.payload.decode())
        data["temperature"] = payload.get("temperature", 0)
        data["humidite"] = payload.get("humidite", 0)
        data["pot"] = payload.get("pot", 0)
        data["ir"] = payload.get("ir", 0)

        # Ajout à l’historique
        t = time.strftime("%H:%M:%S")
        history["time"].append(t)
        history["temperature"].append(data["temperature"])
        history["humidite"].append(data["humidite"])
        history["pot"].append(data["pot"])
        history["ir"].append(data["ir"])

    except Exception as e:
        print("Erreur JSON :", e)


# ---------------------------------------------------------
#  CONNEXION MQTT
# ---------------------------------------------------------
client = mqtt.Client()
client.on_message = on_message

try:
    client.connect("172.161.53.116", 1883, 60)
    client.subscribe("noeud/operateur")
    client.loop_start()
except:
    st.error("❌ Impossible de se connecter au broker MQTT")


# ---------------------------------------------------------
#  INTERFACE STREAMLIT
# ---------------------------------------------------------

# GAUGES ---------------------------------------------------
def gauge(label, value, minv, maxv, color):
    option = {
        "series": [{
            "type": "gauge",
            "progress": {"show": True},
            "axisLine": {"lineStyle": {"color": [[1, color]]}},
            "detail": {"formatter": "{value}"},
            "data": [{"value": value, "name": label}],
            "min": minv,
            "max": maxv
        }]
    }
    st_echarts(option, height="240px")


col1, col2, col3, col4 = st.columns(4)
with col1:
    gauge("Température (°C)", data["temperature"], 0, 100, "red")
with col2:
    gauge("Humidité (%)", data["humidite"], 0, 100, "blue")
with col3:
    gauge("Potentiomètre", data["pot"], 0, 4095, "orange")
with col4:
    gauge("IR (Flamme=1)", data["ir"], 0, 1, "green" if data["ir"] == 0 else "red")


# GRAPHIQUES ------------------------------------------------
st.subheader("📈 Graphiques en temps réel")

df = pd.DataFrame(history)

if len(df) > 1:
    st.line_chart(df[["temperature", "humidite"]])
    st.line_chart(df[["pot"]])
    st.line_chart(df[["ir"]])
else:
    st.info("En attente de données MQTT...")


# AUTO-REFRESH ----------------------------------------------
time.sleep(0.3)
st.experimental_rerun()
