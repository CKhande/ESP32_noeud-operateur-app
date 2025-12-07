# ---------------------------------------------------------
#  DASHBOARD STREAMLIT 100% MQTT CLOUD FIXED
# ---------------------------------------------------------

import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
import plotly.graph_objects as go

# ---------------------------------------------------------
#  CONFIG STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard ESP32", layout="wide")
st.title("📡 Dashboard ESP32 - Temps Réel")
st.write("Données reçues via MQTT (⚠️ Broker Cloud requis)")

# ---------------------------------------------------------
#  AUTO REFRESH
# ---------------------------------------------------------
st.experimental_set_query_params(_=time.time())

# ---------------------------------------------------------
#  SESSION STATE (CRITICAL SECTION)
# ---------------------------------------------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.data = {"temperature": 0, "humidite": 0, "pot": 0, "ir": 0}
    st.session_state.history = {
        "time": [], "temperature": [], "humidite": [], "pot": [], "ir": []
    }

# ---------------------------------------------------------
#  MQTT CALLBACK (SAFE)
# ---------------------------------------------------------
def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode()
        print("Message MQTT brut :", raw)

        try:
            payload = json.loads(raw)
        except:
            print("JSON invalide :", raw)
            return

        # Bloquer tant que les variables Streamlit ne sont pas prêtes
        if "data" not in st.session_state or "history" not in st.session_state:
            print("⚠️ Callback ignoré : session_state pas prêt")
            return

        # Mise à jour des données
        st.session_state.data.update({
            "temperature": payload.get("temperature", 0),
            "humidite": payload.get("humidite", 0),
            "pot": payload.get("pot", 0),
            "ir": payload.get("ir", 0),
        })

        # Historique
        t = time.strftime("%H:%M:%S")
        hist = st.session_state.history

        hist["time"].append(t)
        hist["temperature"].append(st.session_state.data["temperature"])
        hist["humidite"].append(st.session_state.data["humidite"])
        hist["pot"].append(st.session_state.data["pot"])
        hist["ir"].append(st.session_state.data["ir"])

    except Exception as e:
        print("ERREUR CALLBACK MQTT :", e)

# ---------------------------------------------------------
#  MQTT CONNECTION
# ---------------------------------------------------------
BROKER = "172.161.53.116"
PORT = 1883
TOPIC = "noeud/operateur"

client = mqtt.Client()
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.subscribe(TOPIC)
    client.loop_start()
except:
    st.error("❌ Impossible de se connecter au broker MQTT")
    st.stop()

# ---------------------------------------------------------
#  GAUGES
# ---------------------------------------------------------
def plot_gauge(value, title, minv, maxv, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge={"axis": {"range": [minv, maxv]}, "bar": {"color": color}}
    ))
    st.plotly_chart(fig, use_container_width=True, height=260)


d = st.session_state.data

col1, col2, col3, col4 = st.columns(4)
with col1: plot_gauge(d["temperature"], "Température (°C)", 0, 100, "red")
with col2: plot_gauge(d["humidite"], "Humidité (%)", 0, 100, "blue")
with col3: plot_gauge(d["pot"], "Potentiomètre", 0, 4095, "orange")
with col4: plot_gauge(d["ir"], "IR (Flamme)", 0, 1, "green" if d["ir"] == 0 else "red")

# ---------------------------------------------------------
#  GRAPHIQUES
# ---------------------------------------------------------
st.subheader("📈 Graphiques en temps réel")

df = pd.DataFrame(st.session_state.history)

if len(df) > 2:
    st.line_chart(df[["temperature", "humidite"]])
    st.line_chart(df[["pot"]])
    st.line_chart(df[["ir"]])
else:
    st.info("En attente de données MQTT…")
