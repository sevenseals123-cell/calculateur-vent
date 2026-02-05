import streamlit as st
import math
import numpy as np
import pandas as pd

# Configuration
st.set_page_config(page_title="Pilotage - Wind Drift Pro", layout="wide")

st.title("🚢 Calculateur de Contrôlabilité Avancé")

# --- SIDEBAR (Caractéristiques Navire) ---
st.sidebar.header("⚙️ Caractéristiques du Navire")
lpp = st.sidebar.number_input("Lpp (m)", value=330.0)
tirant_air = st.sidebar.number_input("Tirant d'air total (m)", value=55.0)
draft = st.sidebar.number_input("Tirant d'eau actuel (m)", value=12.5)
cb = st.sidebar.number_input("Coefficient Cb", value=0.7)
cp = st.sidebar.slider("Coefficient de porosité (Cp)", 0.6, 1.0, 0.8)

# Calcul automatique du fardage latéral (Aw)
aw_eff = lpp * tirant_air * cp
st.sidebar.info(f"Fardage latéral estimé : {int(aw_eff)} m²")

# --- ZONE PRINCIPALE ---
st.subheader("📊 Conditions Environnementales")
col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    vent_moyen = st.slider("Vent moyen (kn)", 0, 60, 20)
    facteur_rafale = st.slider("Facteur Rafale", 1.0, 2.0, 1.3, step=0.1)
    v_eff = vent_moyen * facteur_rafale

with col_input2:
    # OPTION SECTEUR DU VENT
    secteur_vent = st.selectbox(
        "Provenance du vent (Secteur)",
        ["Travers (60°-120°)", "De l'avant (20°-60°)", "De l'arrière (120°-160°)"]
    )
    # Coefficient correcteur de force selon l'angle (simplifié pour pilotage)
    coef_angle = 1.0 if "Travers" in secteur_vent else (0.6 if "avant" in secteur_vent else 0.4)
    
    drift_angle = st.slider("Angle de dérive cible (°)", 0.5, 15.0, 7.0, step=0.5)

with col_input3:
    vitesse_actuelle = st.number_input("Vitesse actuelle (kn)", value=3.5)
    marge = st.slider("Marge Pilote (kn)", 0.0, 3.0, 1.0)

# --- CALCULS ---
sw = lpp * draft
# Coefficient kβ avec prise en compte du secteur du vent
kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw) * coef_angle

# Vitesse minimale requise
v_min = v_eff * math.sqrt(kb / drift_angle)
v_reco = v_min + marge

# --- AFFICHAGE ---
st.divider()
res1, res2, res3 = st.columns(3)

with res1:
    st.metric("Vitesse Min. Requise", f"{round(v_min, 2)} kn")
with res2:
    st.metric("Vitesse Recommandée", f"{round(v_reco, 2)} kn", delta=f"+{marge} kn")
with res3:
    if vitesse_actuelle >= v_min:
        st.success(f"Statut : MANŒUVRABLE")
    else:
        st.error(f"Statut : DANGER (Dérive excessive)")

# --- GRAPHIQUE ---
st.subheader("📈 Sensibilité au vent")
vents_sim = np.linspace(10, 60, 50)
# On applique le coef_angle ici aussi pour que le graphique soit cohérent
vitesses_sim = vents_sim * facteur_rafale * math.sqrt(kb / drift_angle)

df_sim = pd.DataFrame({
    'Vent (knots)': vents_sim,
    'Vitesse Requise (knots)': vitesses_sim
})

st.line_chart(df_sim.set_index('Vent (knots)'))
