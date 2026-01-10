# ---------------------------------------------------------
# STREAMLIT – CONTROLE LED IO2 PARTAGÉ (2 ESP32)
# ---------------------------------------------------------

import streamlit as st
import paho.mqtt.client as mqtt
import json

# ---------------- MQTT CONFIG ----------------
BROKER = "51.103.239.173"
PORT = 1883
TOPIC_LED = "noeud/operateur/cmd"

# ---------------- MQTT SEND ----------------
def send_led_command(state: int):
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)

    payload = json.dumps({
        "led": state
    })

    client.publish(TOPIC_LED, payload, qos=0, retain=False)
    client.disconnect()

# ---------------- UI ----------------
st.set_page_config(page_title="LED ESP32 Partagée", layout="centered")

st.title("💡 Contrôle LED IO2 – ESP32 (MOI + ELLE)")
st.write("Commande MQTT unique → les deux ESP32 réagissent en même temps")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔵 ALLUMER LED"):
        send_led_command(1)
        st.success("LED IO2 ALLUMÉE chez les deux ESP32")

with col2:
    if st.button("⚫ ÉTEINDRE LED"):
        send_led_command(0)
        st.success("LED IO2 ÉTEINTE chez les deux ESP32")
