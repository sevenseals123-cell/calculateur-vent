import streamlit as st
import math
import pandas as pd
import numpy as np

# --- CONFIGURATION & STYLE ---
st.set_page_config(page_title="DSS Pilotage - Cpt. Dialmy", page_icon="🚢", layout="wide")

footer_style = """
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f0f2f6; color: #31333F; 
    text-align: center; padding: 10px; font-size: 14px; font-weight: bold; border-top: 2px solid #0073e6; z-index: 100; }
    </style>
    <div class="footer"><p>© 2026 - Développé par Cpt. Dialmy | Navigation & Docking Expert</p></div>
"""

# --- SIDEBAR : CARACTÉRISTIQUES NAVIRE ---
st.sidebar.header("🚢 Configuration du Navire")
type_navire = st.sidebar.selectbox("Type de Navire", ["Porte-conteneurs (Grand)", "Pétrolier (VLCC/Suezmax)", "Vraquier (Capesize)", "Méthanier (LNGC)"])

ship_defaults = {
    "Porte-conteneurs (Grand)": {"cb": 0.70, "cp": 0.85, "hair": 55.0},
    "Pétrolier (VLCC/Suezmax)": {"cb": 0.85, "cp": 0.70, "hair": 35.0},
    "Vraquier (Capesize)": {"cb": 0.82, "cp": 0.75, "hair": 30.0},
    "Méthanier (LNGC)": {"cb": 0.75, "cp": 0.90, "hair": 45.0}
}
defaults = ship_defaults[type_navire]

lpp = st.sidebar.number_input("Lpp (m)", value=330.0)
tirant_air = st.sidebar.number_input("Tirant d'air (m)", value=defaults["hair"])
draft = st.sidebar.number_input("Tirant d'eau (m)", value=12.5)
cb = st.sidebar.number_input("Coefficient Cb", value=defaults["cb"])
cp = st.sidebar.slider("Coefficient de porosité (Cp)", 0.5, 1.0, defaults["cp"])
puissance_kw = st.sidebar.number_input("Puissance Moteur (kW)", value=45000)
bow_thruster_kw = st.sidebar.number_input("Bow Thruster (kW)", value=2500)

# Constantes et Conversions
poussee_machine_t = (puissance_kw / 100) * 1.3
bow_thruster_t = (bow_thruster_kw / 100) * 1.2
aw_eff = lpp * tirant_air * cp
sw = lpp * draft

st.title("⚓ Système d'Aide à la Décision - Cpt. Dialmy")

tabs = st.tabs(["🚀 Navigation (Transit)", "🏗️ Docking Mode (Manœuvre)"])

# ---------------------------------------------------------
# ONGLET 1 : NAVIGATION (Transit & Dérive)
# ---------------------------------------------------------
with tabs[0]:
    st.header("🌊 Analyse de Dérive en Transit")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💨 Vent")
        vent_moyen = st.slider("Vent moyen (kn)", 0, 60, 20)
        facteur_rafale = st.slider("Facteur Rafale", 1.0, 2.0, 1.3)
        v_eff = vent_moyen * facteur_rafale
        secteur = st.selectbox("Secteur", ["Travers", "Avant", "Arrière"])
        coef_angle = 1.0 if secteur == "Travers" else (0.6 if secteur == "Avant" else 0.4)

    with col2:
        st.subheader("🚢 Vitesse & Courant")
        v_surface = st.number_input("Vitesse Surface (kn)", value=3.5, min_value=0.1)
        v_courant = st.number_input("Vitesse Courant (kn)", value=1.0)
        dir_courant = st.selectbox("Direction Courant", ["Portant", "Contraire", "Travers"])

    with col3:
        st.subheader("🎯 Cible")
        drift_tolere = st.slider("Angle de dérive toléré (°)", 0.5, 15.0, 7.0)

    # Calculs Physiques
    force_vent_t = (0.5 * 1.225 * ((v_eff * 0.514)**2) * aw_eff * coef_angle) / 9806
    kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw) * coef_angle
    
    # Vitesse Critique : Vitesse à laquelle la dérive dépasse la tolérance
    v_critique = v_eff * math.sqrt(kb / drift_tolere)
    crab_angle = math.degrees(math.atan((v_eff * 0.15 * coef_angle) / v_surface))
    force_requise_rem = max(0.0, force_vent_t * (1 - (v_surface / v_critique)**2)) if v_surface < v_critique else 0.0

    st.divider()
    
    # --- NOUVELLE SECTION : DIAGNOSTIC D'AUTONOMIE ---
    st.subheader("📋 Diagnostic de Tenue de Route")
    diag1, diag2 = st.columns([1, 2])
    
    with diag1:
        st.metric("Vitesse Critique", f"{round(v_critique, 1)} kn", help="Vitesse minimale pour tenir la dérive sans aide.")
        st.metric("Crab Angle", f"{round(crab_angle, 1)}°")

    with diag2:
        if v_surface >= v_critique:
            st.success(f"✅ **Vitesse Suffisante** : À {v_surface} kn, le navire génère assez de portance hydrodynamique pour maintenir la dérive sous les {drift_tolere}°.")
            st.info(f"Marge de sécurité : {round(v_surface - v_critique, 1)} kn au-dessus du seuil critique.")
        else:
            manque_v = round(v_critique - v_surface, 1)
            st.error(f"⚠️ **Vitesse Insuffisante** : La dérive réelle dépassera {drift_tolere}°. Le navire 'tombe' sous le vent.")
            st.write(f"Pour stabiliser le navire, vous devez soit :")
            st.write(f"- Augmenter la vitesse de **{manque_v} kn**.")
            st.write(f"- Faire appel à une poussée de remorquage de **{round(force_requise_rem)} T**.")

    # GRAPHIQUE D'ANALYSE
    st.subheader("📈 Courbe de Puissance vs Vitesse")
    v_range = np.linspace(0.5, max(12.0, v_critique + 2), 50)
    f_rem = [max(0.0, force_vent_t * (1 - (v / v_critique)**2)) if v < v_critique else 0.0 for v in v_range]
    df_plot = pd.DataFrame({"Vitesse (kn)": v_range, "Besoin Remorquage (T)": f_rem})
    st.line_chart(df_plot.set_index("Vitesse (kn)"))

# ---------------------------------------------------------
# ONGLET 2 : DOCKING MODE (Manœuvre)
# ---------------------------------------------------------
with tabs[1]:
    st.header("🛠️ Docking Mode & Tactiques de Quai")
    dcol1, dcol2 = st.columns(2)
    
    with dcol1:
        v_dock = st.slider("Vent au quai (kn)", 0, 60, 15, key="dv")
        manoeuvre = st.radio("Opération", ["Accostage (Poussant)", "Appareillage (Plaquant)"])
    with dcol2:
        tug_dock_bp = st.number_input("BP par remorqueur (T)", value=60, key="dock_bp")
        nb_tugs_dock = st.slider("Nombre de remorqueurs", 0, 4, 2, key="dock_nb")

    force_stat = (0.5 * 1.225 * ((v_dock * 0.514)**2) * aw_eff * 1.0) / 9806
    bilan = (bow_thruster_t + (nb_tugs_dock * tug_dock_bp)) - force_stat

    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Force Vent", f"{round(force_stat)} T")
    res2.metric("Bow Thruster", f"{round(bow_thruster_t)} T")
    res3.metric("Marge Sécurité", f"{round(bilan)} T", delta=f"{round(bilan)} T")

    st.subheader("📍 Recommandations de Placement")
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("### 🗺️ Positionnement")
        if nb_tugs_dock >= 2:
            st.write("- **Tug 1 :** Épaulement Avant / **Tug 2 :** Hanche Arrière.")
        elif nb_tugs_dock == 1:
            st.write("- **Tug unique :** À l'Arrière. Le Bow Thruster gère l'avant.")
    with t2:
        st.markdown("### ⚙️ Tactique")
        if manoeuvre == "Appareillage (Plaquant)":
            st.error("🚩 **VENT PLAQUANT** : Travailler à la tire (capelé). Décoller l'arrière en priorité.")
        else:
            st.success("🏁 **VENT POUSSANT** : Travailler en appui (pousse). Remorqueurs en freins actifs.")

st.markdown(footer_style, unsafe_allow_html=True)
