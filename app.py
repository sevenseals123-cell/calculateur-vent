import streamlit as st
import math

# --- CONFIGURATION & STYLE ---
st.set_page_config(
    page_title="DSS Pilotage - Cpt. Dialmy",
    page_icon="🚢",
    layout="wide"
)

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
        <p>© 2026 - Développé par Cpt. Dialmy | Navigation & Docking Expert</p>
    </div>
"""

# --- SIDEBAR : CONFIGURATION NAVIRE ---
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

# Conversions de base
poussee_machine_t = (puissance_kw / 100) * 1.3
bow_thruster_t = (bow_thruster_kw / 100) * 1.2 
aw_eff = lpp * tirant_air * cp
sw = lpp * draft

st.title("⚓ Système d'Aide à la Décision - Cpt. Dialmy")

# --- SECTION : MÉTHODOLOGIE ---
with st.expander("📚 Méthodologie & Physique des calculs"):
    st.markdown("""
    * **Vent :** $F_w = 0.5 \cdot \\rho \cdot V^2 \cdot A \cdot C_x$.
    * **Dérive :** Basée sur le ratio entre la force aérodynamique et la portance hydrodynamique de la carène.
    * **Bollard Pull :** Ratio standard de $1.2$ T pour $100$ kW pour les propulseurs de tunnel.
    """)

tabs = st.tabs(["🚀 Navigation (Route & Dérive)", "🏗️ Docking Mode (Accostage/Appareillage)"])

# ---------------------------------------------------------
# ONGLET 1 : NAVIGATION (RECONSTRUIT ET VÉRIFIÉ)
# ---------------------------------------------------------
with tabs[0]:
    st.header("🌊 Navigation en Transit")
    n1, n2, n3 = st.columns(3)
    
    with n1:
        st.subheader("💨 Vent")
        vent_moyen = st.slider("Vent moyen (kn)", 0, 60, 20, key="nav_v")
        facteur_rafale = st.slider("Facteur Rafale", 1.0, 2.0, 1.3)
        v_eff = vent_moyen * facteur_rafale
        secteur_vent = st.selectbox("Secteur", ["Travers", "Avant", "Arrière"], key="nav_sec")
        coef_angle = 1.0 if secteur_vent == "Travers" else (0.6 if secteur_vent == "Avant" else 0.4)

    with n2:
        st.subheader("🚢 Vitesse & Courant")
        v_surface = st.number_input("Vitesse Surface (kn)", value=3.5, min_value=0.1)
        v_courant = st.number_input("Vitesse Courant (kn)", value=1.0)
        dir_courant = st.selectbox("Direction Courant", ["Portant", "Contraire", "Travers"])

    with n3:
        st.subheader("🎯 Cible de Dérive")
        drift_tolere = st.slider("Angle de dérive toléré (°)", 0.5, 15.0, 7.0)

    # Calculs Navigation
    force_vent_t = (0.5 * 1.225 * ((v_eff * 0.514)**2) * aw_eff * coef_angle) / 9806
    kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw) * coef_angle
    v_critique = v_eff * math.sqrt(kb / drift_tolere)
    crab_angle = math.degrees(math.atan((v_eff * 0.15 * coef_angle) / v_surface))
    force_requise_rem = max(0.0, force_vent_t * (1 - (v_surface / v_critique)**2)) if v_surface < v_critique else 0.0

    st.divider()
    v_res1, v_res2, v_res3 = st.columns(3)
    v_res1.metric("Force Vent", f"{round(force_vent_t)} T")
    v_res2.metric("Crab Angle Recommandé", f"{round(crab_angle, 1)}°", delta="AU VENT")
    
    # Calcul SOG (Vitesse Fond)
    if dir_courant == "Portant": sog = v_surface + v_courant
    elif dir_courant == "Contraire": sog = v_surface - v_courant
    else: sog = math.sqrt(v_surface**2 + v_courant**2)
    v_res3.metric("Vitesse Fond (SOG)", f"{round(sog, 2)} kn")

    st.subheader("🚜 Analyse du Remorquage en Transit")
    tr1, tr2 = st.columns([1, 2])
    with tr1:
        bp_unit = st.number_input("Bollard Pull / Tug (T)", value=60, key="nav_bp")
        nb_tugs_nav = st.slider("Nombre de remorqueurs", 1, 4, 2, key="nav_nb")
        bp_total_nav = bp_unit * nb_tugs_nav
    with tr2:
        if force_requise_rem > bp_total_nav:
            st.error(f"❌ Danger : Manque {round(force_requise_rem - bp_total_nav)} T de poussée pour contrer la dérive.")
        elif force_requise_rem > 0:
            st.warning(f"⚠️ Assistance nécessaire : {round(force_requise_rem)} T requises.")
        else:
            st.success("✅ Navire autonome : La vitesse surface est suffisante pour contrer le fardage.")

# ---------------------------------------------------------
# ONGLET 2 : DOCKING MODE (AVEC RECOMMANDATIONS TACTIQUES)
# ---------------------------------------------------------
with tabs[1]:
    st.header("🛠️ Docking Mode & Placement Tactique")
    st.info("Vitesse ≈ 0. Analyse de la pression statique et des appuis.")
    
    d1, d2 = st.columns(2)
    with d1:
        v_dock = st.slider("Vent au quai (kn)", 0, 60, 15, key="d_v")
        manoeuvre = st.radio("Opération", ["Accostage (Vent Poussant)", "Appareillage (Vent Plaquant)"])
    with d2:
        tug_bp_dock = st.number_input("Bollard Pull / Tug (T)", value=60, key="d_bp")
        nb_tugs_dock = st.slider("Nombre de remorqueurs", 0, 4, 2, key="d_nb")
    
    # Calcul Force Statique
    force_statique = (0.5 * 1.225 * ((v_dock * 0.514)**2) * aw_eff * 1.0) / 9806
    bilan_dock = (bow_thruster_t + (nb_tugs_dock * tug_bp_dock)) - force_statique

    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Pression Vent", f"{round(force_statique)} T")
    res2.metric("Poussée Thruster", f"{round(bow_thruster_t)} T")
    res3.metric("Marge de Sécurité", f"{round(bilan_dock)} T", delta=f"{round(bilan_dock)} T")

    st.subheader("📍 Recommandations de Placement & Tactique")
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        st.markdown("### 🗺️ Positionnement des Moyens")
        if nb_tugs_dock >= 2:
            st.write("1. **Remorqueur Avant :** Épaulement (Shoulder).")
            st.write("2. **Remorqueur Arrière :** Hanche (Quarter).")
            st.write("3. **Bow Thruster :** Utiliser pour affiner l'angle de l'étrave.")
        elif nb_tugs_dock == 1:
            st.write("1. **Remorqueur :** Priorité à l'arrière (Hanche).")
            st.write("2. **Bow Thruster :** Gère seul le décollage/appui de l'avant.")

    with t_col2:
        st.markdown("### ⚙️ Mode de Travail")
        if manoeuvre == "Appareillage (Vent Plaquant)":
            st.error("🚩 **VENT PLAQUANT :** Travailler impérativement **à la tire** (capelé).")
            st.write("- Tirez l'arrière en premier pour dégager l'hélice.")
            st.write("- Maintenez l'avant au propulseur pendant que le remorqueur arrière écarte le cul.")
        else:
            st.success("🏁 **VENT POUSSANT :** Travailler **en appui** (à la pousse).")
            st.write("- Utilisez les remorqueurs comme 'freins' actifs.")
            st.write("- Vitesse d'approche recommandée : < 0.15 m/s.")

st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown(footer_style, unsafe_allow_html=True)
