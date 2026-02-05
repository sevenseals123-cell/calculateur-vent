import streamlit as st
import math

st.set_page_config(page_title="Pilotage - Calculateur Vent", layout="centered")

st.title("🚢 Calculateur de Dérive et Vitesse")

# --- FORMULAIRE DE SAISIE ---
with st.form("my_form"):
    st.subheader("Paramètres à saisir")
    
    col1, col2 = st.columns(2)
    with col1:
        lpp = st.number_input("Lpp (m)", value=330.0)
        draft = st.number_input("Tirant d'eau (m)", value=12.5)
        cb = st.number_input("Coefficient Cb", value=0.7)
        aw_eff = st.number_input("Fardage effectif (m²)", value=12500.0)
    
    with col2:
        vent = st.number_input("Vent moyen (kn)", value=20.0)
        rafale = st.number_input("Facteur rafale (ex: 1.3 pour 26kts)", value=1.3)
        drift = st.number_input("Angle de dérive souhaité (°)", value=7.0)
    
    submit = st.form_submit_button("CALCULER")

# --- LOGIQUE DE CALCUL ---
if submit:
    # Vent effectif
    v_eff = vent * rafale
    # Surface immergée
    sw = lpp * draft
    # Coefficient de dérive (kβ) basé sur votre formule
    kb = 0.1 * (cb + 0.5 * draft / lpp) * math.sqrt(aw_eff / sw)
    
    # Vitesse minimale requise
    if drift > 0:
        v_min = v_eff * math.sqrt(kb / drift)
    else:
        v_min = 0
    
    v_reco = v_min + 1.0  # Marge pilote

    # --- AFFICHAGE ---
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Vitesse Min. Requise", f"{round(v_min, 2)} kn")
    c2.metric("Vitesse Recommandée", f"{round(v_reco, 2)} kn")

    if v_min > 3.5:
        st.error(f"⚠️ DANGER : À 3.5 kts, vous ne tiendrez pas {drift}° de dérive. Il faut au moins {round(v_min, 2)} kts.")
    else:
        st.success(f"✅ LOGIQUE : À 3.5 kts, le navire peut maintenir cet angle.")
