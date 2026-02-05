import streamlit as st
import math
import numpy as np
import pandas as pd

# Configuration professionnelle
st.set_page_config(page_title="Pilotage - Wind Drift Pro", layout="wide")

st.title("🚢 Ship Controllability & Wind Drift Calculator")

# --- BARRE LATÉRALE (Paramètres fixes du navire) ---
st.sidebar.header("⚙️ Caractéristiques du Navire")
lpp = st.sidebar.number_input("Lpp (m)", value=330.0)
draft = st.sidebar.number_input("Tirant d'eau (m)", value=12.5)
cb = st.sidebar.number_input("Coefficient Cb", value=0.7)
aw_eff = st.sidebar.number_input("Fardage effectif (m²)", value=12500.0)
marge = st.sidebar.slider("Marge Pilote (kn)", 0.0, 3.0, 1.0)

# --- ZONE PRINCIPALE (Variables dynamiques) ---
st.subheader("📊 Conditions Temps Réel")
col_input1, col_input2 = st.columns(2)

with col_input1:
    vent_moyen = st.slider("Vent moyen (kn)", 0, 60, 20)
    facteur_rafale = st.slider("Facteur Rafale", 1.0, 2.0, 1.3, step=0.1)

with col_input2:
    drift_angle = st.slider("Angle de dérive souhaité (°)", 0.5, 15.0, 7.0, step=0.5)
    vitesse_actuelle = st.number_input("Vitesse actuelle du navire (kn)", value=3.5)

# --- LOGIQUE DE CALCUL ---
v_eff = vent_moyen * facteur_rafale
sw = lpp * draft
# Formule du coefficient kβ
kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw)

# Vitesse minimale pour tenir l'angle
v_min = v_eff * math.sqrt(kb / drift_angle)
v_reco = v_min + marge

# --- AFFICHAGE DES RÉSULTATS ---
st.divider()
res1, res2, res3 = st.columns(3)

with res1:
    st.metric("Vitesse Min. Requise", f"{round(v_min, 2)} kn")
with res2:
    st.metric("Vitesse Recommandée", f"{round(v_reco, 2)} kn", delta=f"+{marge} kn")
with res3:
    status = "✅ OK" if vitesse_actuelle >= v_min else "❌ DANGER"
    st.metric("Statut Maniabilité", status)

# --- ALERTE VISUELLE ---
if vitesse_actuelle < v_min:
    st.error(f"⚠️ CAPACITÉ DE MANOEUVRE INSUFFISANTE : Le navire va dériver de plus de {drift_angle}°. Augmentez la vitesse à {round(v_min, 1)} kts.")

# --- GRAPHIQUE D'ANTICIPATION ---
st.divider()
st.subheader("📈 Courbe de Controllabilité (Vitesse vs Vent)")

# Simulation de la vitesse requise pour différents vents
vents_sim = np.linspace(10, 60, 50)
vitesses_sim = vents_sim * facteur_rafale * math.sqrt(kb / drift_angle)

df_sim = pd.DataFrame({
    'Vent (knots)': vents_sim,
    'Vitesse Requise (knots)': vitesses_sim
})

st.line_chart(df_sim.set_index('Vent (knots)'))
st.caption(f"Graphique basé sur un facteur rafale de {facteur_rafale} et une dérive de {drift_angle}°")
