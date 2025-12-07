# ---------------------------------------------------------
#  DASHBOARD STREAMLIT MQTT (VERSION AVEC LOCK)
# ---------------------------------------------------------

import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
import plotly.graph_objects as go
import threading

# ---------------------------------------------------------
#  VERROU GLOBAL POUR SYNCHRONISER MQTT & STREAMLIT
# ---------------------------------------------------------
ready_lock = threading.Event()   # reste bloqué tant que Streamlit n'est pas prêt


# ---------------------------------------------------------
#  CONFIG STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard ESP32", layout="wide")
st.title("📡 Dashboard ESP32 - Temps Réel")
st.write("Données reçues via MQTT (⚠️ Broker Cloud requis)")

st.experimental_set_query_params(refresh=time.time())

# ---------------------------------------------------------
#  SESSION STATE
# ---------------------------------------------------------
if "data" not in st.session_state:
    st.session_state.data = {"temperature": 0, "humidite": 0, "pot": 0, "ir": 0}

if "history" not in st.session_state:
    st.session_state.history = {
        "time": [], "temperature": [], "humidite": [], "pot": [], "ir": []
    }

# 🔥 IMPORTANT : maintenant Streamlit est INITIALISÉ
ready_lock.set()


# ---------------------------------------------------------
#  MQTT CALLBACK
# ---------------------------------------------------------
def on_message(client, userdata, msg):

    # 🔥 Attendre que Streamlit ait créé session_state
    ready_lock.wait()

    raw = msg.payload.decode()
    print("Message MQTT brut :", raw)

    try:
        payload = json.loads(raw)
    except:
        print("Erreur JSON :", raw)
        return

    # Mise à jour des données
    st.session_state.data.update({
        "temperature": payload.get("temperature", 0),
        "humidite": payload.get("humidite", 0),
        "pot": payload.get("pot", 0),
        "ir": payload.get("ir", 0)
    })

    # Historique
    t = time.strftime("%H:%M:%S")
    hist = st.session_state.history
    hist["time"].append(t)
    hist["temperature"].append(st.session_state.data["temperature"])
    hist["humidite"].append(st.session_state.data["humidite"])
    hist["pot"].append(st.session_state.data["pot"])
    hist["ir"].append(st.session_state.data["ir"])


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
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)


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

if len(df) > 1:
    st.line_chart(df[["temperature", "humidite"]])
    st.line_chart(df[["pot"]])
    st.line_chart(df[["ir"]])
else:
    st.info("En attente de données MQTT…")
