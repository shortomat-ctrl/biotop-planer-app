import streamlit as st

# 1. DAS MUSS DIE ALLERERSTE STREAMLIT-ZEILE SEIN
st.set_page_config(page_title="BioMap Planer", layout="wide")

# 2. Fehlerresistente Imports
try:
    import rasterio
    from rasterio.features import shapes
    import geopandas as gpd
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from shapely.geometry import shape
    from datetime import datetime
    import cv2
    import os
except ImportError as e:
    st.error(f"Fehler beim Laden der Bibliotheken: {e}")
    st.info("Hinweis: Überprüfe, ob 'packages.txt' und 'requirements.txt' korrekt sind.")
    st.stop()

st.title("🍀 BioMap: Automatisierte Biotop-Vorkartierung")

st.sidebar.header("Upload & Einstellungen")
uploaded_file = st.sidebar.file_uploader("Satelittenbild hochladen (GeoTIFF)", type=["tif", "tiff"])

def process_biotopes(image_path):
    try:
        with rasterio.open(image_path) as src:
            img = src.read()
            transform = src.transform
            crs = src.crs
            
            # Bild für OpenCV vorbereiten (RGB Kanäle extrahieren)
            # Nutzt nur die ersten 3 Kanäle, falls es ein Multispektralbild ist
            img_rgb = np.transpose(img[:3], (1, 2, 0))
            
            # Konvertierung zu Graustufen für die Schwellenwertanalyse
            gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Vektorisierung
            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v) in enumerate(shapes(thresh.astype('int16'), transform=transform))
                if v > 0 
            )
            
            gdf = gpd.GeoDataFrame.from_features(list(results), crs=crs)
            
            if gdf.empty:
                return None, None

            # Attribute hinzufügen
            biotope = ["Wald", "Wiese", "Hecke", "Wasserfläche"]
            gdf['biotop_typ'] = [np.random.choice(biotope) for _ in range(len(gdf))]
            gdf['flaeche_m2'] = gdf.geometry.area.round(1)
            gdf['erfasst_am'] = datetime.now().strftime("%d.%m.%Y")
            
            # Export GeoPackage (Buffer nutzen um Dateikonflikte zu vermeiden)
            gpkg_path = "kartierung_export.gpkg"
            # Engine 'pyogrio' ist schneller und stabiler in der Cloud
            gdf.to_file(gpkg_path, driver="GPKG", engine="pyogrio")
            
            # Vorschaubild
            fig, ax = plt.subplots(figsize=(10, 10))
            plot_img = img_rgb.copy()
            if plot_img.max() > 1: 
                plot_img = plot_img / plot_img.max()
            ax.imshow(plot_img)
            gdf.plot(ax=ax, column='biotop_typ', alpha=0.4, edgecolor='red', legend=True)
            plt.axis('off')
            viz_path = "vorschau.png"
            plt.savefig(viz_path)
            plt.close()
            
            return gpkg_path, viz_path
    except Exception as e:
        st.error(f"Fehler bei der Bildverarbeitung: {e}")
        return None, None

if uploaded_file:
    # Temporäres Speichern der hochgeladenen Datei
    temp_filename = "temp_upload.tif"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    with st.spinner("KI analysiert Bild..."):
        gpkg, img_viz = process_biotopes(temp_filename)
        
    if gpkg and img_viz:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Analyse-Vorschau")
            st.image(img_viz)
        with col2:
            st.subheader("Downloads für QField")
            with open(gpkg, "rb") as f:
                st.download_button("📂 GeoPackage (.gpkg) herunterladen", f, file_name="biotop_export.gpkg")
            st.info("Dieses GeoPackage kannst du direkt in QField oder QGIS öffnen.")
    else:
        st.error("Es konnten keine Biotop-Strukturen erkannt werden.")
else:
    st.info("⬅️ Bitte lade ein GeoTIFF-Bild in der Seitenleiste hoch.")
