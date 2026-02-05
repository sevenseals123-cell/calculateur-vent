import streamlit as st
import math
import numpy as np
import pandas as pd

st.set_page_config(page_title="Pilotage Expert - DSS", layout="wide")
st.title("⚓ Système d'Aide à la Décision : Manœuvre & Navigation")

# --- SIDEBAR : DONNÉES NAVIRE ---
st.sidebar.header("⚙️ Caractéristiques Navire")
lpp = st.sidebar.number_input("Lpp (m)", value=330.0)
tirant_air = st.sidebar.number_input("Tirant d'air (m)", value=55.0)
draft = st.sidebar.number_input("Tirant d'eau (m)", value=12.5)
cb = st.sidebar.number_input("Coefficient Cb", value=0.7)
cp = st.sidebar.slider("Coefficient de porosité (Cp)", 0.6, 1.0, 0.8)
puissance_max_t = st.sidebar.number_input("Poussée Machine Max (Tonnes)", value=120.0)

aw_eff = lpp * tirant_air * cp

# --- SECTION 1 : VENT & DÉRIVE (CRAB ANGLE) ---
st.header("🌬️ Vent & Dynamique de Dérive")
c1, c2, c3 = st.columns(3)

with c1:
    vent_moyen = st.slider("Vent moyen (kn)", 0, 60, 20)
    facteur_rafale = st.slider("Facteur Rafale", 1.0, 2.0, 1.3)
    v_eff = vent_moyen * facteur_rafale
    secteur_vent = st.selectbox("Provenance Vent", ["Travers", "Avant", "Arrière"])

with c2:
    # CALCUL DU CRAB ANGLE (Dérive angulaire nécessaire)
    # Approximation basée sur la force latérale vs vitesse navire
    v_surface = st.number_input("Vitesse Surface (kn)", value=3.5, min_value=0.1)
    coef_angle = 1.0 if "Travers" in secteur_vent else (0.6 if "Avant" in secteur_vent else 0.4)
    
    # Calcul simplifié du Crab Angle théorique
    crab_angle = math.degrees(math.atan((v_eff * 0.1) / v_surface)) * coef_angle
    st.metric("Crab Angle Estimé", f"{round(crab_angle, 1)}°")

with c3:
    force_vent_t = (0.5 * 1.225 * ((v_eff * 0.514)**2) * aw_eff * coef_angle) / 9806
    st.metric("Force Vent Latérale", f"{round(force_vent_t)} T")

# --- SECTION 2 : COURANT & VECTEUR RÉEL (SOG/COG) ---
st.header("🌊 Effet du Courant & Vecteur Fond")
cc1, cc2, cc3 = st.columns(3)

with cc1:
    v_courant = st.number_input("Vitesse du Courant (kn)", value=1.0)
    dir_courant = st.selectbox("Direction Courant", ["Portant (Même sens)", "Contraire", "Travers bâbord", "Travers tribord"])

with cc2:
    # Calcul Vitesse Fond (SOG)
    if "Portant" in dir_courant: sog = v_surface + v_courant
    elif "Contraire" in dir_courant: sog = v_surface - v_courant
    else: sog = math.sqrt(v_surface**2 + v_courant**2)
    st.metric("Vitesse Fond (SOG)", f"{round(sog, 2)} kn")

with cc3:
    # Limite Machine
    charge_machine = (force_vent_t / puissance_max_t) * 100
    st.write(f"Utilisation de la puissance : **{round(charge_machine)}%**")
    st.progress(min(charge_machine/100, 1.0))

# --- SECTION 3 : REMORQUAGE & TACTIQUE ---
st.header("🚜 Assistance Remorquage")
t1, t2 = st.columns(2)

with t1:
    type_tug = st.radio("Type de Remorqueur", ["ASD", "Conventionnel"])
    bp_dispo = st.number_input("Bollard Pull Total (T)", value=60)

with t2:
    if charge_machine > 80:
        st.error("🚨 LIMITE MACHINE ATTEINTE : Le moteur seul ne peut pas contrer le vent. Remorqueurs indispensables.")
    elif force_vent_t > bp_dispo:
        st.warning(f"⚠️ CAPACITÉ REMORQUAGE LIMITE : Manque {round(force_vent_t - bp_dispo)} T de poussée.")
    else:
        st.success("✅ Marges de manœuvre suffisantes.")

# --- GRAPHIQUE DE SÉCURITÉ ---
st.divider()
st.subheader("📈 Enveloppe de Sécurité : Vitesse Navire vs Force Vent")
v_range = np.linspace(1, 15, 30)
# Force nécessaire pour maintenir l'équilibre
force_req = (force_vent_t / (v_range + 0.1)) * 2 # Relation inverse simplifiée
df_sec = pd.DataFrame({'Vitesse Navire (kn)': v_range, 'Stabilité Manœuvre (Indice)': force_req})
st.line_chart(df_sec.set_index('Vitesse Navire (kn)'))
