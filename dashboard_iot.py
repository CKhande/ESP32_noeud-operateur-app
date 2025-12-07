# ---------------------------------------------------------
#  DASHBOARD STREAMLIT EN TEMPS RÉEL (MQTT → GAUGES + GRAPH)
#  Version 100% compatible Streamlit Cloud
# ---------------------------------------------------------

import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
from streamlit_echarts import st_echarts

# ---------------------------------------------------------
#  CONFIG STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard ESP32", layout="wide")

st.title("📡 Dashboard ESP32 - Temps Réel")
st.write("Données reçues via MQTT (⚠️ Broker Cloud requis)")

# ---------------------------------------------------------
#  AUTO REFRESH COMPATIBLE STREAMLIT CLOUD
# ---------------------------------------------------------
# Force la page à se rafraîchir en changeant l'URL à chaque chargement
st.experimental_set_query_params(ts=str(time.time()))

# ---------------------------------------------------------
#  SESSION STATE (SAVE DATA)
# ---------------------------------------------------------
if "data" not in st.session_state:
    st.session_state.data = {"temperature": 0, "humidite": 0, "pot": 0, "ir": 0}

if "history" not in st.session_state:
    st.session_state.history = {
        "time": [],
        "temperature": [],
        "humidite": [],
        "pot": [],
        "ir": []
    }

# ---------------------------------------------------------
#  MQTT CALLBACK
# ---------------------------------------------------------
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        st.session_state.data["temperature"] = payload.get("temperature", 0)
        st.session_state.data["humidite"] = payload.get("humidite", 0)
        st.session_state.data["pot"] = payload.get("pot", 0)
        st.session_state.data["ir"] = payload.get("ir", 0)

        t = time.strftime("%H:%M:%S")
        h = st.session_state.history

        h["time"].append(t)
        h["temperature"].append(st.session_state.data["temperature"])
        h["humidite"].append(st.session_state.data["humidite"])
        h["pot"].append(st.session_state.data["pot"])
        h["ir"].append(st.session_state.data["ir"])

    except Exception as e:
        print("Erreur JSON :", e)

# ---------------------------------------------------------
#  MQTT CONNECTION (CLOUD COMPATIBLE)
# ---------------------------------------------------------

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "esp32/noeud"

client = mqtt.Client()
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.subscribe(TOPIC)
    client.loop_start()
except:
    st.error("❌ Impossible de se connecter au broker MQTT (Cloud)")

# ---------------------------------------------------------
#  GAUGE FUNCTION
# ---------------------------------------------------------
def gauge(label, value, minv, maxv, color):
    option = {
        "series": [{
            "type": "gauge",
            "progress": {"show": True, "width": 15},
            "axisLine": {"lineStyle": {"width": 15, "color": [[1, color]]}},
            "pointer": {"itemStyle": {"color": "#444"}},
            "detail": {"formatter": "{value}", "fontSize": 20},
            "data": [{"value": value, "name": label}],
            "min": minv,
            "max": maxv
        }]
    }
    st_echarts(option, height="260px")

# ---------------------------------------------------------
#  DISPLAY GAUGES
# ---------------------------------------------------------
data = st.session_state.data

col1, col2, col3, col4 = st.columns(4)
with col1:
    gauge("Température (°C)", data["temperature"], 0, 100, "#FF4B4B")
with col2:
    gauge("Humidité (%)", data["humidite"], 0, 100, "#3A7DFF")
with col3:
    gauge("Potentiomètre", data["pot"], 0, 4095, "#FFA500")
with col4:
    gauge("IR (Flamme)", data["ir"], 0, 1, "#00CC66" if data["ir"] == 0 else "#FF0000")

# ---------------------------------------------------------
#  GRAPHES
# ---------------------------------------------------------
st.subheader("📈 Graphiques en temps réel")

df = pd.DataFrame(st.session_state.history)

if len(df) > 2:
    st.line_chart(df[["temperature", "humidite"]])
    st.line_chart(df[["pot"]])
    st.line_chart(df[["ir"]])
else:
    st.info("En attente de données MQTT...")
