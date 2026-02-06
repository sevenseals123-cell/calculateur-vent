import streamlit as st
import math
import numpy as np
import pandas as pd

# --- CONFIGURATION & STYLE ---
st.set_page_config(
    page_title="DSS Pilotage - Cpt. Dialmy",
    page_icon="🚢",
    layout="wide"
)

# --- STYLE CSS POUR LE FOOTER ---
footer_style = """
    <style>
    .footer {
        position: fixed;
        left: 0; bottom: 0; width: 100%;
        background-color: #f0f2f6; color: #31333F;
        text-align: center; padding: 10px;
        font-size: 14px; font-weight: bold;
        border-top: 2px solid #0073e6; z-index: 100;
    }
    </style>
    <div class="footer">
        <p>© 2026 - Développé par Cpt. Dialmy | Docking & Navigation Expert</p>
    </div>
"""

# --- SIDEBAR : CONFIGURATION DU NAVIRE ---
st.sidebar.header("🚢 Caractéristiques du Navire")
type_navire = st.sidebar.selectbox(
    "Type de Navire",
    ["Porte-conteneurs (Grand)", "Pétrolier (VLCC/Suezmax)", "Vraquier (Capesize)", "Méthanier (LNGC)"]
)

ship_defaults = {
    "Porte-conteneurs (Grand)": {"cb": 0.70, "cp": 0.85, "hair": 55.0},
    "Pétrolier (VLCC/Suezmax)": {"cb": 0.85, "cp": 0.70, "hair": 35.0},
    "Vraquier (Capesize)": {"cb": 0.82, "cp": 0.75, "hair": 30.0},
    "Méthanier (LNGC)": {"cb": 0.75, "cp": 0.90, "hair": 45.0}
}
defaults = ship_defaults[type_navire]

lpp = st.sidebar.number_input("Lpp (m)", value=330.0)
tirant_air = st.sidebar.number_input("Tirant d'air total (m)", value=defaults["hair"])
draft = st.sidebar.number_input("Tirant d'eau actuel (m)", value=12.5)
cb = st.sidebar.number_input("Coefficient Cb", value=defaults["cb"])
cp = st.sidebar.slider("Coefficient de porosité (Cp)", 0.5, 1.0, defaults["cp"])
puissance_kw = st.sidebar.number_input("Puissance Moteur (kW)", value=45000)
bow_thruster_kw = st.sidebar.number_input("Puissance Bow Thruster (kW)", value=2500)

# Conversions Techniques (Standard Naval)
poussee_machine_t = (puissance_kw / 100) * 1.3
bow_thruster_t = (bow_thruster_kw / 100) * 1.2 
aw_eff = lpp * tirant_air * cp
sw = lpp * draft

st.title("⚓ Système d'Aide à la Décision : Manœuvre & Navigation")

# --- NOUVELLE SECTION : AIDE & MÉTHODOLOGIE ---
with st.expander("📚 Comprendre la Physique du Calcul (Méthodologie)"):
    st.write("Cet outil repose sur les principes de la dynamique des fluides et les standards de l'industrie navale.")
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("""
        **1. Force du Vent (Aérodynamique)** La force est calculée via la pression dynamique :  
        $$F_w = \\frac{1}{2} \\rho V^2 A C_x$$  
        * $\\rho = 1.225 kg/m^3$ (densité air)
        * $A$ = Surface de fardage latérale effective.
        * $V^2$ = Le carré de la vitesse du vent (pression exponentielle).
        """)
    with m2:
        st.markdown("""
        **2. Correction de Cap (Crab Angle)** Calculé par trigonométrie vectorielle pour maintenir la COG (Course Over Ground) sur la route souhaitée :  
        $$\\alpha_{crab} = \\arctan\\left(\\frac{V_{dérive}}{V_{surface}}\\right)$$
        
        **3. Conversion Puissance/Tonne** * Propulseur : $1.2$ Tonne / $100$ kW.  
        * Machine (CP hélice) : $1.3$ Tonne / $100$ kW.
        """)

# --- NAVIGATION PAR ONGLETS ---
tabs = st.tabs(["🚀 Navigation (Route & Dérive)", "🏗️ Docking Mode (Accostage/Appareillage)"])

# --- ONGLET 1 : NAVIGATION ---
with tabs[0]:
    st.header("🌊 Conditions de Navigation en Route")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("💨 Vent")
        vent_moyen = st.slider("Vent moyen (kn)", 0, 60, 20)
        facteur_rafale = st.slider("Facteur Rafale", 1.0, 2.0, 1.3)
        v_eff = vent_moyen * facteur_rafale
        secteur_vent = st.selectbox("Secteur du vent", ["Travers", "Avant", "Arrière"])
        coef_angle = 1.0 if secteur_vent == "Travers" else (0.6 if secteur_vent == "Avant" else 0.4)

    with c2:
        st.subheader("🚢 Vitesse & Courant")
        v_surface = st.number_input("Vitesse Surface (kn)", value=3.5, min_value=0.1)
        v_courant = st.number_input("Vitesse Courant (kn)", value=1.0)
        dir_courant = st.selectbox("Direction Courant", ["Portant", "Contraire", "Travers"])

    with c3:
        st.subheader("🎯 Cible de Dérive")
        drift_angle_subi = st.slider("Angle de dérive subi toléré (°)", 0.5, 15.0, 7.0)

    # Calculs Navigation
    force_vent_t = (0.5 * 1.225 * ((v_eff * 0.514)**2) * aw_eff * coef_angle) / 9806
    kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw) * coef_angle
    v_critique = v_eff * math.sqrt(kb / drift_angle_subi)
    crab_angle = math.degrees(math.atan((v_eff * 0.15 * coef_angle) / v_surface))
    force_requise_rem = max(0.0, force_vent_t * (1 - (v_surface / v_critique)**2)) if v_surface < v_critique else 0.0

    st.divider()
    v1, v2, v3 = st.columns(3)
    with v1: st.metric("Dérive (Subie)", f"{round(drift_angle_subi, 1)}°")
    with v2: st.metric("Crab Angle (Correction)", f"{round(crab_angle, 1)}°", delta="CAP AU VENT")
    with v3: 
        sog = v_surface + v_courant if dir_courant == "Portant" else (v_surface - v_courant if dir_courant == "Contraire" else v_surface)
        st.metric("Vitesse Fond (SOG)", f"{round(sog, 2)} kn")

    st.divider()
    t1, t2 = st.columns([1, 2])
    with t1:
        type_tug = st.radio("Type de Remorqueur", ["ASD (Omnidirectionnel)", "Conventionnel"], key="nav_tug")
        bp_unitaire = st.number_input("Bollard Pull (T)", value=60, key="nav_bp")
        nb_tugs = st.slider("Nombre de remorqueurs", 1, 4, 2, key="nav_nb")
        bp_total = bp_unitaire * nb_tugs
    with t2:
        st.subheader("🚜 Tactiques en Route")
        if force_requise_rem > bp_total: st.error(f"❌ Puissance insuffisante ! Manque {round(force_requise_rem - bp_total)} T.")
        elif force_requise_rem > 0: st.warning(f"⚠️ Remorqueurs doivent fournir {round(force_requise_rem)} T.")
        else: st.success("✅ Navire autonome à cette vitesse.")
        
        util_machine = (force_vent_t / poussee_machine_t) * 100
        st.write(f"Charge Moteur : {round(util_machine)}%")
        st.progress(min(util_machine/100, 1.0))

# --- ONGLET 2 : DOCKING MODE ---
with tabs[1]:
    st.header("🛠️ Docking Mode : Accostage / Appareillage")
    st.info("Analyse statique des forces au quai (Vitesse ≈ 0).")
    
    d1, d2 = st.columns(2)
    with d1:
        v_dock = st.slider("Vent au quai (kn)", 0, 60, 15)
        manoeuvre = st.radio("Opération", ["Accostage (Vent Poussant au quai)", "Appareillage (Vent Plaquant au quai)"])
    
    with d2:
        tug_bp_dock = st.number_input("Bollard Pull Tug (T)", value=60, key="dock_bp")
        nb_tugs_dock = st.slider("Nombre de remorqueurs", 0, 4, 2, key="dock_nb")
        force_statique = (0.5 * 1.225 * ((v_dock * 0.514)**2) * aw_eff * 1.0) / 9806
        
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Poussée du Vent", f"{round(force_statique)} T")
    res2.metric("Poussée Bow Thruster", f"{round(bow_thruster_t)} T")
    
    bilan_dock = (bow_thruster_t + (nb_tugs_dock * tug_bp_dock)) - force_statique
    color = "normal" if bilan_dock > 0 else "inverse"
    res3.metric("Marge de Puissance", f"{round(bilan_dock)} T", delta=f"{round(bilan_dock)} T", delta_color=color)

    st.subheader("📍 Tactique Cpt. Dialmy")
    if manoeuvre == "Appareillage (Vent Plaquant au quai)":
        if bilan_dock < 5: st.error("🚨 **ALERTE :** Puissance critique. Difficile de décoller sans renfort.")
        else: st.markdown(f"- **Conseil :** Utiliser le Bow Thruster à 100% et capeler les remorqueurs côté large.")
    else:
        st.warning("⚖️ **CONSEIL :** Vent poussant. Utiliser les remorqueurs pour amortir l'approche.")

# --- FOOTER ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown(footer_style, unsafe_allow_html=True)
