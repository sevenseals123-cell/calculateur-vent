import streamlit as st
import math
import numpy as np
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Pilotage Pro - DSS Master", layout="wide")

st.title("⚓ Système d'Aide à la Décision : Manœuvre & Remorquage")

# --- SIDEBAR : CARACTÉRISTIQUES NAVIRE ---
st.sidebar.header("⚙️ Fiche Technique Navire")
lpp = st.sidebar.number_input("Lpp (m)", value=330.0)
tirant_air = st.sidebar.number_input("Tirant d'air total (m)", value=55.0)
draft = st.sidebar.number_input("Tirant d'eau actuel (m)", value=12.5)
cb = st.sidebar.number_input("Coefficient Cb", value=0.7)
cp = st.sidebar.slider("Coefficient de porosité (Cp)", 0.6, 1.0, 0.8)
poussée_machine_max = st.sidebar.number_input("Poussée Machine Max (T)", value=120.0)

# Calculs de base
aw_eff = lpp * tirant_air * cp
sw = lpp * draft

# --- SECTION 1 : ENVIRONNEMENT & VECTEURS ---
st.header("🌊 Environnement & Vecteurs")
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Vent")
    vent_moyen = st.slider("Vent moyen (kn)", 0, 60, 20)
    facteur_rafale = st.slider("Facteur Rafale", 1.0, 2.0, 1.3)
    v_eff = vent_moyen * facteur_rafale
    secteur_vent = st.selectbox("Secteur du vent", ["Travers", "Avant", "Arrière"])
    coef_angle = 1.0 if secteur_vent == "Travers" else (0.6 if secteur_vent == "Avant" else 0.4)

with c2:
    st.subheader("Courant & Vitesse")
    v_surface = st.number_input("Vitesse Surface (kn)", value=3.5, min_value=0.1)
    v_courant = st.number_input("Vitesse Courant (kn)", value=1.0)
    dir_courant = st.selectbox("Direction Courant", ["Portant", "Contraire", "Travers"])
    
    # Calcul SOG (Vitesse Fond)
    if dir_courant == "Portant": sog = v_surface + v_courant
    elif dir_courant == "Contraire": sog = v_surface - v_courant
    else: sog = math.sqrt(v_surface**2 + v_courant**2)

with c3:
    st.subheader("Cible de Manœuvre")
    drift_angle_cible = st.slider("Angle de dérive souhaité (°)", 0.5, 15.0, 7.0)
    # Calcul du Crab Angle théorique (Vecteur Vent/Vitesse)
    crab_angle = math.degrees(math.atan((v_eff * 0.12) / v_surface)) * coef_angle
    st.metric("Crab Angle Estimé", f"{round(crab_angle, 1)}°")

# --- CALCULS PHYSIQUES ---
# Force du vent en Tonnes
force_vent_t = (0.5 * 1.225 * ((v_eff * 0.514)**2) * aw_eff * coef_angle) / 9806

# Vitesse critique de contrôle (Hydrodynamique)
kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw) * coef_angle
v_critique = v_eff * math.sqrt(kb / drift_angle_cible)

# Force requise par les remorqueurs pour tenir l'angle de dérive cible
# Si vitesse_navire < v_critique, les remorqueurs doivent compenser la différence de force
force_requise_remorquage = max(0.0, force_vent_t * (1 - (v_surface / v_critique)**2)) if v_surface < v_critique else 0.0

# --- SECTION 2 : ANALYSE DE LA PUISSANCE ---
st.divider()
st.header("🚜 Analyse du Remorquage & Tactiques")
t1, t2 = st.columns([1, 2])

with t1:
    type_tug = st.radio("Type de Remorqueur", ["ASD (Omnidirectionnel)", "Conventionnel"])
    bp_unitaire = st.number_input("Bollard Pull par remorqueur (T)", value=60)
    nb_tugs = st.slider("Nombre de remorqueurs", 1, 4, 2)
    bp_total = bp_unitaire * nb_tugs

with t2:
    st.subheader("📋 Recommandations de Puissance")
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Force Vent Latérale", f"{round(force_vent_t)} T")
    col_res2.metric("Poussée Requise (Tug)", f"{round(force_requise_remorquage)} T", delta_color="inverse")
    
    if force_requise_remorquage > bp_total:
        st.error(f"❌ ALERTE : Puissance de remorquage insuffisante ! Il manque {round(force_requise_remorquage - bp_total)} T pour tenir {drift_angle_cible}° de dérive.")
    elif force_requise_remorquage > 0:
        st.warning(f"⚠️ Action requise : Les remorqueurs doivent exercer une poussée de {round(force_requise_remorquage)} T pour stabiliser le navire.")
    else:
        st.success("✅ Équilibre atteint : Le navire tient son angle par sa propre vitesse.")

    # TACTIQUES SPÉCIFIQUES
    st.info("**Conseils Tactiques :**")
    if secteur_vent == "Travers":
        st.markdown(f"- **Placement :** 1 Tug à l'épaulement, 1 au fessier.\n- **Méthode :** {'Pousser' if type_tug == 'ASD' else 'Capeler (Tirer)'} sur le côté sous le vent.")
    elif secteur_vent == "Avant":
        st.markdown("- **Placement :** Tug à l'avant (Center Lead).\n- **Méthode :** Capeler pour contrôler l'abattée et aider à la giration.")
    else:
        st.markdown("- **Placement :** Tug en Escort (Arrière).\n- **Méthode :** Contrôler l'énergie cinétique et stabiliser la route fond.")

# --- SECTION 3 : LIMITES MACHINE ---
st.divider()
st.subheader("⚙️ État des Limites Machine")
util_machine = (force_vent_t / poussée_machine_max) * 100
c_m1, c_m2 = st.columns([1, 3])
c_m1.metric("Charge Machine", f"{round(util_machine)}%")
c_m2.progress(min(util_machine/100, 1.0))
if util_machine > 85:
    st.error("🚨 Risque de perte de contrôle machine. Puissance moteur insuffisante face au vent.")

# --- GRAPHIQUE ---
st.subheader("📈 Enveloppe de Manœuvrabilité")
v_range = np.linspace(1, 10, 20)
# Calcul de la force Tug nécessaire selon la vitesse du navire
f_tug_range = [max(0.0, force_vent_t * (1 - (v / v_critique)**2)) if v < v_critique else 0.0 for v in v_range]
df_plot = pd.DataFrame({'Vitesse Navire (kn)': v_range, 'Poussée Tug Nécessaire (T)': f_tug_range})
st.line_chart(df_plot.set_index('Vitesse Navire (kn)'))
