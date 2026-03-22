import streamlit as st

# MUSS die erste Streamlit-Anweisung sein
st.set_page_config(page_title="BioMap Debug", layout="wide")

st.title("🌿 BioMap Boot-Check")

st.write("Versuche Bibliotheken zu laden...")

try:
    import numpy as np
    st.success(f"✅ NumPy geladen (Version: {np.__version__})")
    
    import rasterio
    st.success("✅ Rasterio erfolgreich geladen")
    
    import geopandas as gpd
    st.success("✅ Geopandas erfolgreich geladen")
    
    import cv2
    st.success("✅ OpenCV erfolgreich geladen")

    st.balloons()
    st.info("Alle Systeme bereit! Jetzt können wir deinen Analyse-Code einfügen.")

except Exception as e:
    st.error(f"❌ Fehler beim Laden der Bibliotheken: {e}")
    st.warning("Das liegt meist an inkompatiblen Versionen in requirements.txt oder packages.txt.")

with st.sidebar:
    st.header("Upload-Test")
    test_upload = st.file_uploader("Test Upload", type=["tif"])
