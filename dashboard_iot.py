# ---------------------------------------------------------
# DASHBOARD STREAMLIT (POLLING MQTT + COMMANDES LED)
# ---------------------------------------------------------

import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
import plotly.graph_objects as go

# ---------------------------------------------------------
# SESSION STATE INITIALISATION
# ---------------------------------------------------------
if "data" not in st.session_state:
    st.session_state.data = {"temperature": 0, "humidite": 0, "pot": 0, "ir": 0}

if "history" not in st.session_state:
    st.session_state.history = {
        "time": [], "temperature": [], "humidite": [], "pot": [], "ir": []
    }

if "led_state" not in st.session_state:
    st.session_state.led_state = 0  # LED OFF par défaut

# ---------------------------------------------------------
# MQTT CONFIG
# ---------------------------------------------------------
BROKER = "172.161.53.116"
PORT = 1883
TOPIC = "noeud/operateur"
TOPIC_CMD = "noeud/operateur/cmd"   # Commande LED IO2

# ---------------------------------------------------------
# ENVOI COMMANDE LED
# ---------------------------------------------------------
def send_led_command(state):
    client = mqtt.Client()
    try:
        client.connect(BROKER, PORT, 60)
        payload = json.dumps({"led": state})
        client.publish(TOPIC_CMD, payload)
        client.disconnect()
    except Exception as e:
        st.error(f"Erreur MQTT LED: {e}")

# ---------------------------------------------------------
# POLLING MQTT
# ---------------------------------------------------------
def poll_mqtt():
    client = mqtt.Client()
    messages = []

    def on_message(client, userdata, msg):
        try:
            messages.append(msg.payload.decode())
        except:
            pass

    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, 60)
        client.subscribe(TOPIC)
        client.loop_start()
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
    except:
        return None

    if messages:
        return messages[-1]
    return None

# ---------------------------------------------------------
# LECTURE DES DONNÉES MQTT
# ---------------------------------------------------------
raw = poll_mqtt()

if raw:
    try:
        payload = json.loads(raw)

        st.session_state.data.update({
            "temperature": payload.get("temperature", 0),
            "humidite": payload.get("humidite", 0),
            "pot": payload.get("pot", 0),
            "ir": payload.get("ir", 0)
        })

        t = time.strftime("%H:%M:%S")
        hist = st.session_state.history
        hist["time"].append(t)
        hist["temperature"].append(st.session_state.data["temperature"])
        hist["humidite"].append(st.session_state.data["humidite"])
        hist["pot"].append(st.session_state.data["pot"])
        hist["ir"].append(st.session_state.data["ir"])

    except:
        st.write("Erreur JSON :", raw)

# ---------------------------------------------------------
# UI PRINCIPALE
# ---------------------------------------------------------

st.title("📡 Dashboard ESP32 - Temps Réel")
st.write("Données reçues via MQTT + Contrôle LED IO2")

d = st.session_state.data

# ---------------------------------------------------------
# GAUGES
# ---------------------------------------------------------
def plot_gauge(value, title, minv, maxv, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge={"axis": {"range": [minv, maxv]}, "bar": {"color": color}}
    ))
    st.plotly_chart(fig, use_container_width=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    plot_gauge(d["temperature"], "Température (°C)", 0, 100, "red")

with col2:
    plot_gauge(d["humidite"], "Humidité (%)", 0, 100, "blue")

with col3:
    plot_gauge(d["pot"], "Potentiomètre", 0, 4095, "orange")

with col4:
    plot_gauge(d["ir"], "IR (Flamme)", 0, 1, "green" if d["ir"] == 0 else "red")

st.markdown("---")

# ---------------------------------------------------------
# 🟦 CONTRÔLE LED IO2 (PLACÉ JUSTE APRÈS LES GAUGES)
# ---------------------------------------------------------
st.header("💡 Contrôle de la LED IO2 (ESP32)")

colA, colB = st.columns(2)

with colA:
    if st.button("🔵 Allumer la LED IO2"):
        st.session_state.led_state = 1
        send_led_command(1)
        st.success("LED IO2 allumée")

with colB:
    if st.button("⚫ Éteindre la LED IO2"):
        st.session_state.led_state = 0
        send_led_command(0)
        st.success("LED IO2 éteinte")

st.markdown("---")

# ---------------------------------------------------------
# GRAPHIQUES TEMPS RÉEL
# ---------------------------------------------------------
st.subheader("📈 Graphiques en temps réel")

df = pd.DataFrame(st.session_state.history)

if len(df) > 1:
    st.line_chart(df[["temperature", "humidite"]])
    st.line_chart(df["pot"])
    st.line_chart(df["ir"])
else:
    st.info("En attente de premières données MQTT…")

# AUTO REFRESH TOUTES LES SECONDES
st.rerun()
