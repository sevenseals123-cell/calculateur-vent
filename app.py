import streamlit as st
import math
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="DSS Pilotage - Cpt. Dialmy", page_icon="🚢", layout="wide")

footer_style = """
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f0f2f6; color: #31333F; 
    text-align: center; padding: 10px; font-size: 14px; font-weight: bold; border-top: 2px solid #0073e6; z-index: 100; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    <div class="footer"><p>© 2026 - Développé par Cpt. Dialmy | Navigation & Docking</p></div>
"""

# Constantes Physiques Globales
RHO_AIR = 1.225      # Densité de l'air (kg/m3)
G = 9806.65          # Conversion Newtons -> Tonnes métriques
KN_TO_MS = 0.51444   # Nœuds vers m/s

# --- 2. SIDEBAR : CARACTÉRISTIQUES NAVIRE ---
st.sidebar.header("🚢 Configuration du Navire")
type_navire = st.sidebar.selectbox("Type de Navire", ["Porte-conteneurs (Grand)", "Pétrolier (VLCC/Suezmax)", "Vraquier (Capesize)", "Méthanier (LNGC)"])

# Dictionnaire des profils par défaut
ship_defaults = {
    "Porte-conteneurs (Grand)": {"cb": 0.70, "cp": 0.85, "hair": 55.0},
    "Pétrolier (VLCC/Suezmax)": {"cb": 0.85, "cp": 0.70, "hair": 35.0},
    "Vraquier (Capesize)": {"cb": 0.82, "cp": 0.75, "hair": 30.0},
    "Méthanier (LNGC)": {"cb": 0.75, "cp": 0.90, "hair": 45.0}
}
defaults = ship_defaults[type_navire]

with st.sidebar.expander("📐 Dimensions & Hydrodynamique", expanded=True):
    lpp = st.number_input("Lpp (m)", value=330.0, step=10.0)
    tirant_air = st.number_input("Tirant d'air (m)", value=defaults["hair"], step=1.0)
    draft = st.number_input("Tirant d'eau (m)", value=12.5, step=0.5)
    cb = st.number_input("Coefficient Cb", value=defaults["cb"], step=0.01)
    cp = st.slider("Porosité Fardage (Cp)", 0.5, 1.0, defaults["cp"], step=0.05)

with st.sidebar.expander("⚙️ Motorisation & Propulseurs", expanded=True):
    puissance_kw = st.number_input("Puissance Moteur (kW)", value=45000, step=1000)
    bow_thruster_kw = st.number_input("Bow Thruster (kW)", value=2500, step=100)

# Pré-calculs structurels
poussee_machine_t = (puissance_kw / 100) * 1.3
bow_thruster_t = (bow_thruster_kw / 100) * 1.2
aw_eff = lpp * tirant_air * cp # Surface fardage effective
sw = lpp * draft               # Surface latérale sous-marine

# --- 3. INTERFACE PRINCIPALE ---
st.title("⚓ Système d'Aide à la Décision (DSS)")
st.markdown("Outil tactique pour l'évaluation du fardage et l'assistance à la manœuvre d'accostage.")

tabs = st.tabs(["🚀 Transit & Fardage", "🏗️ Docking (Accostage / Appareillage)"])

# =========================================================
# ONGLET 1 : TRANSIT & FARDAGE
# =========================================================
with tabs[0]:
    st.header("🌊 Évaluation du Fardage en Transit")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💨 Paramètres Vent")
        vent_moyen = st.slider("Vent moyen (kn)", 0, 60, 20)
        facteur_rafale = st.slider("Facteur Rafale", 1.0, 2.0, 1.3, step=0.1)
        v_eff = vent_moyen * facteur_rafale
        secteur = st.selectbox("Secteur d'incidence", ["Travers", "Avant", "Arrière"])
        coef_angle = 1.0 if secteur == "Travers" else (0.6 if secteur == "Avant" else 0.4)

    with col2:
        st.subheader("🚢 Cinématique")
        v_surface = st.number_input("Vitesse Surface (kn)", value=3.5, min_value=0.1, step=0.5)
        v_courant = st.number_input("Vitesse Courant (kn)", value=1.0, step=0.2)
        dir_courant = st.selectbox("Direction Courant", ["Portant", "Contraire", "Travers"])

    with col3:
        st.subheader("🎯 Marge Opérationnelle")
        limite_deviation = st.slider("Tolérance de déviation (°)", 1.0, 15.0, 7.0, step=0.5, help="Limite à partir de laquelle le vent prend le dessus sur la gouverne.")

    # --- MOTEUR PHYSIQUE ---
    # Force du vent en tonnes
    force_vent_t = (0.5 * RHO_AIR * ((v_eff * KN_TO_MS)**2) * aw_eff * coef_angle) / G
    
    # Calcul de la Vitesse Critique de Gouverne
    kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw) * coef_angle
    v_critique = v_eff * math.sqrt(kb / limite_deviation) if limite_deviation > 0 else 0
    
    # Besoin en remorquage si la vitesse est trop faible
    if v_surface < v_critique and v_critique > 0:
        force_requise_rem = max(0.0, force_vent_t * (1 - (v_surface / v_critique)**2))
    else:
        force_requise_rem = 0.0

    st.divider()
    
    # --- DIAGNOSTIC DE ROUTE ---
    st.subheader("📋 Diagnostic de Tenue de Cap")
    diag1, diag2 = st.columns([1, 2])
    
    with diag1:
        st.metric("Vitesse Limite (Steerage)", f"{v_critique:.1f} kn", help="Vitesse minimale requise pour compenser le fardage sans aide.")
        st.metric("Force Vent Subie", f"{force_vent_t:.1f} T")

    with diag2:
        if v_surface >= v_critique:
            st.success(f"✅ **Vitesse de sécurité atteinte** : À {v_surface} kn, le flux d'eau sur le safran est suffisant pour contrer la force du vent.")
            st.info(f"Marge de vitesse : +{v_surface - v_critique:.1f} kn.")
        else:
            manque_v = v_critique - v_surface
            st.error(f"⚠️ **Perte d'efficacité gouverne** : Vitesse insuffisante pour contrer le fardage.")
            st.markdown(f"**Actions correctives requises :**")
            st.markdown(f"- 🟢 Augmenter la vitesse d'au moins **{manque_v:.1f} kn**.")
            st.markdown(f"- 🚜 Ou engager une force de remorquage (Escort) de **{force_requise_rem:.1f} T**.")

    # --- GRAPHIQUE ---
    st.subheader("📈 Profil d'Assistance (Traction requise vs Vitesse)")
    v_range = np.linspace(0.5, max(12.0, v_critique + 2), 50)
    f_rem = [max(0.0, force_vent_t * (1 - (v / v_critique)**2)) if v < v_critique else 0.0 for v in v_range]
    
    df_plot = pd.DataFrame({"Vitesse (kn)": v_range, "Force de Remorquage Requise (T)": f_rem}).set_index("Vitesse (kn)")
    st.area_chart(df_plot, color="#ff4b4b", use_container_width=True)

# =========================================================
# ONGLET 2 : DOCKING (Manœuvre)
# =========================================================
with tabs[1]:
    st.header("🛠️ Analyse Statique d'Accostage & Appareillage")
    dcol1, dcol2 = st.columns(2)
    
    with dcol1:
        v_dock = st.slider("Vent traversier au quai (kn)", 0, 60, 15, key="dv")
        manoeuvre = st.radio("Type d'Opération", ["Accostage (Vent Poussant)", "Appareillage (Vent Plaquant)"])
    with dcol2:
        tug_dock_bp = st.number_input("Bollard Pull par remorqueur (T)", value=60, step=5, key="dock_bp")
        nb_tugs_dock = st.slider("Nombre de remorqueurs engagés", 0, 4, 2, key="dock_nb")

    # Calculs Statiques
    force_stat = (0.5 * RHO_AIR * ((v_dock * KN_TO_MS)**2) * aw_eff) / G
    total_push_pull = bow_thruster_t + (nb_tugs_dock * tug_dock_bp)
    bilan = total_push_pull - force_stat

    st.divider()
    
    # Affichage dynamique des métriques
    res1, res2, res3 = st.columns(3)
    res1.metric("🌪️ Pression du Vent", f"{force_stat:.1f} T")
    res2.metric("⚙️ Force Totale Engagée", f"{total_push_pull:.1f} T", help="Bow Thruster + Remorqueurs")
    
    if bilan >= 0:
        res3.metric("✅ Marge de Sécurité", f"{bilan:.1f} T", delta=f"Surplus de {bilan:.1f} T")
    else:
        res3.metric("❌ Déficit de Force", f"{bilan:.1f} T", delta=f"Manque {abs(bilan):.1f} T", delta_color="inverse")

    # --- RECOMMANDATIONS TACTIQUES ---
    st.subheader("📍 Tactique & Positionnement")
    t1, t2 = st.columns(2)
    
    with t1:
        st.markdown("### 🗺️ Allocation des forces")
        if nb_tugs_dock >= 2:
            st.info("**Configuration Standard :**\n- **Tug 1 :** Épaulement Avant (Équilibrage avec Bow Thruster)\n- **Tug 2 :** Hanche Arrière (Contrôle du pivot)")
        elif nb_tugs_dock == 1:
            st.warning("**Configuration Restreinte :**\n- **Tug unique :** À positionner à la Hanche Arrière.\n- L'étrave doit être gérée exclusivement au Bow Thruster.")
        else:
            st.error("**Manœuvre en propre :** Aucun remorqueur. Forte dépendance au Bow Thruster et à la cinématique.")

    with t2:
        st.markdown("### ⚙️ Consignes Opérationnelles")
        if "Plaquant" in manoeuvre:
            if bilan < 0:
                st.error("🚨 **IMPOSSIBLE D'APPAREILLER** : La force de décollage (Tugs + BT) est inférieure à la pression du vent. Le navire restera plaqué aux défenses.")
            else:
                st.warning("🚩 **VENT PLAQUANT** : Travailler à la tire (capelé). Priorité au décollage de la poupe pour engager l'hélice en sécurité.")
        else:
            if bilan < 0:
                st.error("🚨 **RISQUE D'AVARIE** : Force de retenue insuffisante. L'impact sur les défenses dépassera les limites tolérées.")
            else:
                st.success("🏁 **VENT POUSSANT** : Travailler en appui (pousse). Remorqueurs en freins actifs pour maîtriser la vitesse d'approche latérale.")

# Injection du Footer
st.markdown(footer_style, unsafe_allow_html=True)
