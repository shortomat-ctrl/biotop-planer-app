import streamlit as st
import rasterio
from rasterio.features import shapes
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import shape
from datetime import datetime
import cv2

# Titel der App
st.set_page_config(page_title="BioMap Planer", layout="wide")
st.title("🍀 BioMap: Automatisierte Biotop-Vorkartierung")

st.sidebar.header("Upload & Einstellungen")
uploaded_file = st.sidebar.file_uploader("Satelittenbild hochladen (GeoTIFF)", type=["tif", "tiff"])

def process_biotopes(image_path):
    with rasterio.open(image_path) as src:
        img = src.read()
        transform = src.transform
        crs = src.crs
        
        # Einfache Analyse: Sucht nach grünen Strukturen (Simulation)
        # In einer echten Umgebung würde hier ein KI-Modell (SAM) stehen
        gray = cv2.cvtColor(np.transpose(img[:3], (1, 2, 0)), cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Vektorisierung (Pixel zu Polygonen)
        results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) in enumerate(shapes(thresh.astype('int16'), transform=transform))
            if v > 0 
        )
        
        gdf = gpd.GeoDataFrame.from_features(list(results), crs=crs)
        
        # Attribute für QField hinzufügen
        biotope = ["Wald", "Wiese", "Hecke", "Wasserfläche"]
        gdf['biotop_typ'] = [np.random.choice(biotope) for _ in range(len(gdf))]
        gdf['flaeche_m2'] = gdf.geometry.area.round(1)
        gdf['erfasst_am'] = datetime.now().strftime("%d.%m.%Y")
        gdf['bemerkung'] = "KI-Vorschlag"

        # Export GeoPackage
        gpkg_path = "kartierung_export.gpkg"
        gdf.to_file(gpkg_path, driver="GPKG")
        
        # Vorschaubild erstellen
        fig, ax = plt.subplots(figsize=(10, 10))
        plot_img = np.transpose(img[:3], (1, 2, 0))
        if plot_img.max() > 1: plot_img = plot_img / plot_img.max()
        ax.imshow(plot_img)
        gdf.plot(ax=ax, column='biotop_typ', alpha=0.4, edgecolor='red', legend=True)
        plt.axis('off')
        viz_path = "vorschau.png"
        plt.savefig(viz_path)
        plt.close()
        
        return gpkg_path, viz_path

if uploaded_file:
    with open("temp.tif", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    with st.spinner("KI analysiert Bild..."):
        gpkg, img_viz = process_biotopes("temp.tif")
        
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
    st.warning("Bitte lade ein Bild in der Seitenleiste hoch.")
