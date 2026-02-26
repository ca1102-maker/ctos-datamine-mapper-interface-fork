# ===============================
# 🧬 MedSyn AI — Medical Synonym Assistant (Simplified Display)
# ===============================

import streamlit as st
import pandas as pd
from PIL import Image
import os

# -------------------------------
# PAGE CONFIGURATION
# -------------------------------
st.set_page_config(
    page_title="MedSyn AI: Medical Synonym Assistant",
    page_icon="icon.png",
    layout="wide"
)

# -------------------------------
# HEADER
# -------------------------------
logo_path = "logo.png"
try:
    logo = Image.open(logo_path)
    st.image(logo, width=700)
except Exception:
    st.warning("⚠️ Logo not found. Please place 'logo.png' in the same folder.")

st.markdown(
    """
    <p style='font-size:1.4em; color:#5f6361;'>
    💡I am a semantic assistant trained to unify medical terminology, enabling fast synonym discovery,
    contextual understanding, and data interoperability across biomedical datasets.
    </p>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# LOAD LOCAL CSV BACKUP
# -------------------------------
BACKUP_FILE = "medsyn_backup.csv"

if os.path.exists(BACKUP_FILE):
    try:
        df = pd.read_csv(BACKUP_FILE)
        st.success(f"📁 Loaded local backup data from `{BACKUP_FILE}`")
    except Exception as e:
        st.error(f"❌ Failed to load `{BACKUP_FILE}`: {e}")
        st.stop()
else:
    st.error("❌ Backup file not found. Please add `medsyn_backup.csv` to the repository.")
    st.stop()

# -------------------------------
# CATEGORY + TERM SELECTION
# -------------------------------
categories = sorted(df["Category"].unique())

st.markdown("---")
st.subheader("🔍 Explore Medical Terminology")

selected_category = st.selectbox("Select a category:", categories)
terms = df[df["Category"] == selected_category]["Term"].unique().tolist()
selected_term = st.selectbox("Choose a suggested keyword:", [""] + terms)

# -------------------------------
# DISPLAY OUTPUT (No Chat Mode)
# -------------------------------
prompt = st.text_input("Enter a medical term or NCIT code...", value= "C102193") #selected_term)

if prompt:
    '''# Look up in CSV
    result_row = df[df["Term"].str.lower() == prompt.lower()]
    if not result_row.empty:
        synonyms = result_row.iloc[0]["Synonyms"]
        definition = result_row.iloc[0]["Definition"]'''
    if True:
        try:
            response = requests.post(
                "http://127.0.0.1:8000/exact_match/by_code",
                json={"code": "C102193"), #prompt},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                term = data.get("term", "")
                definition = data.get("definition", "")
            else:
                st.error(f"Backend error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"⚠️ Could not connect to backend: {e}")

        # MedSyn AI icon
        try:
            icon = Image.open("icon.png")
            st.image(icon, width=70)
        except Exception:
            pass

        # Show results (no “Results for ...”)
        st.markdown(
            f"""
            <div style='font-size:1.05em; line-height:1.6em; color:#333;'>
            <b>Synonyms:</b> {term}<br><br>
            <b>Definition:</b> {definition}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"⚠️ No match for '{prompt}' in current reference set. Adding to database pipeline… meanwhile, explore available terms in the dropdown.")

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("---")
st.markdown(
    "<center><p style='color:#9e9e9e;'>MediSyn AI © 2025 | Developed by Scientists for Experts 🎯 Built to Unify Medical Terminology Through Semantic Intelligence</p></center>",
    unsafe_allow_html=True
)
