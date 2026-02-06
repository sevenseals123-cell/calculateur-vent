import streamlit as st
import math

# --- CONFIGURATION & STYLE ---
st.set_page_config(page_title="DSS Pilotage - Cpt. Dialmy", page_icon="🚢", layout="wide")

footer_style = """
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f0f2f6; color: #31333F; 
    text-align: center; padding: 10px; font-size: 14px; font-weight: bold; border-top: 2px solid #0073e6; z-index: 100; }
    </style>
    <div class="footer"><p>© 2026 - Développé par Cpt. Dialmy | Docking & Navigation Expert</p></div>
"""

# --- SIDEBAR : CARACTÉRISTIQUES ---
st.sidebar.header("🚢 Caractéristiques du Navire")
type_navire = st.sidebar.selectbox("Type de Navire", ["Porte-conteneurs", "Pétrolier", "Vraquier", "Méthanier"])

ship_defaults = {
    "Porte-conteneurs": {"cb": 0.70, "cp": 0.85, "hair": 55.0},
    "Pétrolier": {"cb": 0.85, "cp": 0.70, "hair": 35.0},
    "Vraquier": {"cb": 0.82, "cp": 0.75, "hair": 30.0},
    "Méthanier": {"cb": 0.75, "cp": 0.90, "hair": 45.0}
}
defaults = ship_defaults[type_navire]

lpp = st.sidebar.number_input("Lpp (m)", value=330.0)
tirant_air = st.sidebar.number_input("Tirant d'air total (m)", value=defaults["hair"])
draft = st.sidebar.number_input("Tirant d'eau actuel (m)", value=12.5)
cp = st.sidebar.slider("Coefficient de porosité (Cp)", 0.5, 1.0, defaults["cp"])
bow_thruster_kw = st.sidebar.number_input("Puissance Bow Thruster (kW)", value=2500)

# Conversions
bow_thruster_t = (bow_thruster_kw / 100) * 1.2
aw_eff = lpp * tirant_air * cp

st.title("⚓ Système d'Aide à la Décision - Cpt. Dialmy")

with st.expander("📚 Méthodologie"):
    st.write("Calculs basés sur la pression dynamique de l'air et la conversion standard kW/Tonne.")

tabs = st.tabs(["🚀 Navigation", "🏗️ Docking Mode"])

# --- ONGLET 1 : NAVIGATION (Inchangé) ---
with tabs[0]:
    st.header("🌊 Navigation en Route")
    # ... (Code précédent de navigation conservé) ...
    st.info("Utilisez cet onglet pour le transit en chenal (Crab Angle).")

# --- ONGLET 2 : DOCKING MODE (AMÉLIORÉ) ---
with tabs[1]:
    st.header("🛠️ Docking & Placement des Remorqueurs")
    
    col1, col2 = st.columns(2)
    with col1:
        v_dock = st.slider("Vent au quai (kn)", 0, 60, 15)
        manoeuvre = st.radio("Type d'opération", ["Accostage (Vent Poussant)", "Appareillage (Vent Plaquant)"])
    
    with col2:
        tug_bp = st.number_input("Bollard Pull par remorqueur (T)", value=60)
        nb_tugs = st.slider("Nombre de remorqueurs", 0, 4, 2)
        pression_vent = (0.5 * 1.225 * ((v_dock * 0.514)**2) * aw_eff * 1.0) / 9806

    st.divider()

    # Bilan des forces
    force_tugs_total = nb_tugs * tug_bp
    force_dispo = force_tugs_total + bow_thruster_t
    marge = force_dispo - pression_vent

    c1, c2, c3 = st.columns(3)
    c1.metric("Poussée du Vent", f"{round(pression_vent)} T")
    c2.metric("Aide Extérieure (Tugs+BT)", f"{round(force_dispo)} T")
    c3.metric("Marge de Sécurité", f"{round(marge)} T", delta=f"{round(marge)} T")

    # --- NOUVELLE SECTION : PLACEMENT DES REMORQUEURS ---
    st.subheader("🚜 Recommandations de Placement & Tactique")
    
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        st.markdown("### 📍 Positionnement")
        if nb_tugs >= 2:
            st.write("**Remorqueur 1 :** Épaulement avant (Porte-haubans).")
            st.write("**Remorqueur 2 :** Hanche arrière (Au niveau du bloc château).")
        elif nb_tugs == 1:
            st.write("**Remorqueur unique :** À l'arrière (pour contrer l'effet de lacet), utilisez le Bow Thruster pour l'avant.")
        
        st.markdown("### ⚙️ Mode de Travail")
        if manoeuvre == "Appareillage (Vent Plaquant)":
            st.info("👉 **Méthode :** Travailler à la tire (capelé).")
            st.write("- Tirez l'arrière en premier pour dégager l'hélice.")
            st.write("- Utilisez le Bow Thruster pour maintenir l'avant.")
        else:
            st.success("👉 **Méthode :** Travailler à la pousse (appui).")
            st.write("- Gardez les remorqueurs en contact pour amortir la dérive.")
            st.write("- Attention à ne pas créer un moment de rotation excessif.")

    with t_col2:
        st.markdown("### ⚠️ Points d'attention")
        if v_dock > 25:
            st.error("❗ Vent fort : Risque de dépassement des capacités des lignes de remorque.")
        if marge < 10:
            st.warning("⚠️ Marge faible : Envisagez un remorqueur supplémentaire ou attendez une accalmie.")
        
        # Conseil sur le levier
        st.markdown(f"""
        **Répartition de la force :**
        - Force nécessaire à l'Avant : ~{round(pression_vent/2)} T (BT + Tug 1)
        - Force nécessaire à l'Arrière : ~{round(pression_vent/2)} T (Tug 2)
        """)



st.markdown(footer_style, unsafe_allow_html=True)
