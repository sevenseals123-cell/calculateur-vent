import streamlit as st
import math
import numpy as np
import pandas as pd

# --- CONFIGURATION DE LA PAGE & ICÔNE ---
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
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f0f2f6;
        color: #31333F;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
        border-top: 2px solid #0073e6;
        z-index: 100;
    }
    </style>
    <div class="footer">
        <p>© 2026 - Développé par Cpt. Dialmy | Système d'Aide à la Décision (DSS) - Aide Pilotage</p>
    </div>
"""

st.title("⚓ Système d'Aide à la Décision : Manœuvre & Remorquage")

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
poussee_machine_t = (puissance_kw / 100) * 1.3

aw_eff = lpp * tirant_air * cp
sw = lpp * draft

# --- SECTION 1 : ENVIRONNEMENT ---
st.header("🌊 Conditions Environnementales")
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

# --- CALCULS PHYSIQUES ---
force_vent_t = (0.5 * 1.225 * ((v_eff * 0.514)**2) * aw_eff * coef_angle) / 9806
kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw) * coef_angle
v_critique = v_eff * math.sqrt(kb / drift_angle_subi)
crab_angle = math.degrees(math.atan((v_eff * 0.15 * coef_angle) / v_surface))
force_requise_rem = max(0.0, force_vent_t * (1 - (v_surface / v_critique)**2)) if v_surface < v_critique else 0.0

# --- SECTION 2 : ANALYSE DES VECTEURS ---
st.divider()
v1, v2, v3 = st.columns(3)
with v1: st.metric("Dérive (Subie)", f"{round(drift_angle_subi, 1)}°")
with v2: st.metric("Crab Angle (Correction)", f"{round(crab_angle, 1)}°", delta="CAP AU VENT")
with v3: 
    sog = v_surface + v_courant if dir_courant == "Portant" else (v_surface - v_courant if dir_courant == "Contraire" else v_surface)
    st.metric("Vitesse Fond (SOG)", f"{round(sog, 2)} kn")

# --- SECTION 3 : ANALYSE REMORQUAGE COMPLÈTE ---
st.divider()
st.header("🚜 Recommandations Tactiques de Remorquage")
t1, t2 = st.columns([1, 2])

with t1:
    type_tug = st.radio("Type de Remorqueur", ["ASD (Omnidirectionnel)", "Conventionnel"])
    bp_unitaire = st.number_input("Bollard Pull par remorqueur (T)", value=60)
    nb_tugs = st.slider("Nombre de remorqueurs", 1, 4, 2)
    bp_total = bp_unitaire * nb_tugs

with t2:
    st.subheader("📋 Plan de Manœuvre")
    c_res1, c_res2 = st.columns(2)
    c_res1.metric("Force Vent à contrer", f"{round(force_vent_t)} T")
    c_res2.metric("Poussée Tug Nécessaire", f"{round(force_requise_rem)} T")

    if force_requise_rem > bp_total:
        st.error(f"❌ **ALERTE CRITIQUE** : Puissance de remorquage insuffisante ! Manque {round(force_requise_rem - bp_total)} T.")
    elif force_requise_rem > 0:
        st.warning(f"⚠️ **ACTION REQUISE** : Les remorqueurs doivent compenser activement ({round(force_requise_rem)} T).")
    else:
        st.success("✅ **ÉQUILIBRE** : La vitesse du navire suffit à contrer la dérive.")

    with st.expander("📍 Voir le détail du placement et des ordres", expanded=True):
        if secteur_vent == "Travers":
            st.markdown(f"""
            - **Positionnement :** 1 Tug à l'épaulement, 1 au fessier, côté **sous le vent**.
            - **Ordres :** {'Pousser au contact' if type_tug == 'ASD' else 'Capeler sur ligne courte'}.
            - **Objectif :** Annuler la force latérale de {round(force_vent_t)} T.
            """)
        elif secteur_vent == "Avant":
            st.markdown("""
            - **Positionnement :** Tug principal capelé en 'Center Lead' à l'avant.
            - **Ordres :** Contrôler l'abattée du nez face au vent.
            - **Objectif :** Maintenir le Crab Angle sans dérive.
            """)
        else:
            st.markdown("""
            - **Positionnement :** Tug en 'Escort' (Arrière).
            - **Ordres :** Stabiliser le fessier contre les embardées.
            """)

# --- SECTION 4 : LIMITES MACHINE ---
st.divider()
st.subheader("⚙️ Limites de Propulsion du Navire")
util_machine = (force_vent_t / poussee_machine_t) * 100
st.write(f"Utilisation moteur face au vent : **{round(util_machine)}%**")
st.progress(min(util_machine/100, 1.0))

# --- GRAPHIQUE ---
st.subheader("📈 Force Remorqueur Requise selon votre Vitesse Surface")
v_range = np.linspace(1, 10, 20)
f_tug_range = [max(0.0, force_vent_t * (1 - (v / v_critique)**2)) if v < v_critique else 0.0 for v in v_range]
df_plot = pd.DataFrame({'Vitesse Navire (kn)': v_range, 'Force Tug (T)': f_tug_range})
st.line_chart(df_plot.set_index('Vitesse Navire (kn)'))

# --- ESPACE POUR LE FOOTER ---
st.markdown("<br><br><br>", unsafe_allow_html=True)

# --- AFFICHAGE DU FOOTER ---
st.markdown(footer_style, unsafe_allow_html=True)
