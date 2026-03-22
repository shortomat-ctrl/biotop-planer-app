import streamlit as st
import os

# 1. Seite konfigurieren (MUSS die erste Streamlit-Zeile sein)
st.set_page_config(page_title="BioMap Planer", layout="wide")

# 2. Bibliotheken laden
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
except ImportError as e:
    st.error(f"Fehler beim Laden der Bibliotheken: {e}")
    st.stop()

# --- ANALYSE FUNKTION ---
def process_biotopes(image_path):
    try:
        with rasterio.open(image_path) as src:
            img = src.read()
            transform = src.transform
            crs = src.crs
            
            # Bild für Analyse vorbereiten (nur die ersten 3 Kanäle RGB)
            # Wir transponieren von (Channels, Height, Width) zu (Height, Width, Channels)
            img_rgb = np.transpose(img[:3], (1, 2, 0))
            
            # Konvertierung zu Graustufen
            gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            
            # Einfache Segmentierung (Otsu Thresholding)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Vektorisierung: Pixel-Maske zu Polygonen umwandeln
            mask = thresh.astype('int16')
            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v) in enumerate(shapes(mask, transform=transform))
                if v > 0  # Nur "Vordergrund" (Biotop-Kandidaten) extrahieren
            )
            
            gdf = gpd.GeoDataFrame.from_features(list(results), crs=crs)
            
            if gdf.empty:
                return None, None

            # Simulation der KI-Klassifizierung: Attribute hinzufügen
            biotope_typen = ["Wald", "Wiese", "Hecke", "Wasserfläche"]
            gdf['biotop_typ'] = [np.random.choice(biotope_typen) for _ in range(len(gdf))]
            gdf['flaeche_m2'] = gdf.geometry.area.round(1)
            gdf['erfasst_am'] = datetime.now().strftime("%d.%m.%Y")
            gdf['quelle'] = "BioMap KI-Vorschlag"

            # Export als GeoPackage
            gpkg_path = "biotop_export.gpkg"
            gdf.to_file(gpkg_path, driver="GPKG")
            
            # Visualisierung erstellen
            fig, ax = plt.subplots(figsize=(10, 10))
            # Normalisierung für die Anzeige, falls nötig
            plot_img = img_rgb.copy().astype(float)
            if plot_img.max() > 1:
                plot_img /= plot_img.max()
                
            ax.imshow(plot_img)
            gdf.plot(ax=ax, column='biotop_typ', alpha=0.4, edgecolor='red', legend=True)
            plt.axis('off')
            
            viz_path = "vorschau.png"
            plt.savefig(viz_path, bbox_inches='tight')
            plt.close(fig) # Speicher freigeben
            
            return gpkg_path, viz_path
            
    except Exception as e:
        st.error(f"Fehler in der Bildverarbeitung: {e}")
        return None, None

# --- UI INTERFACE ---
st.title("🍀 BioMap: Automatisierte Biotop-Vorkartierung")
st.markdown("""
Lade ein **Satelittenbild (GeoTIFF)** hoch. Die KI erkennt Strukturen und erstellt ein GeoPackage, 
das du direkt in **QGIS** oder **QField** zur Feldkartierung nutzen kannst.
""")

st.sidebar.header("Daten-Upload")
uploaded_file = st.sidebar.file_uploader("GeoTIFF hochladen", type=["tif", "tiff"])

if uploaded_file:
    # Temporäres Speichern
    with open("temp_upload.tif", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    with st.spinner("Analysiere Landschaftsstrukturen..."):
        gpkg, img_viz = process_biotopes("temp_upload.tif")
    
    if gpkg and img_viz:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Analyse-Vorschau")
            st.image(img_viz, use_container_width=True)
            
        with col2:
            st.subheader("Export")
            st.success("Analyse abgeschlossen!")
            
            with open(gpkg, "rb") as f:
                st.download_button(
                    label="📂 GeoPackage für QField herunterladen",
                    data=f,
                    file_name="biotop_vorkartierung.gpkg",
                    mime="application/geopackage+sqlite3"
                )
            
            st.info("""
            **Nächste Schritte:**
            1. GeoPackage in QGIS/QField öffnen.
            2. Vor Ort die KI-Vorschläge prüfen.
            3. Biotop-Typen final bestätigen.
            """)
    else:
        st.warning("Es konnten keine markanten Strukturen erkannt werden. Versuche ein Bild mit höherem Kontrast.")

else:
    st.info("⬅️ Bitte lade ein GeoTIFF in der Seitenleiste hoch, um die Vorkartierung zu starten.")

# Fußzeile
st.divider()
st.caption("Biotop-Planer App | Version 1.0 (Stable)")
