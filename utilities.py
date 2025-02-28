import pandas as pd
import numpy as np
import random

def parse_coord(coord):
    try:
        return float(str(coord).replace(',', '.').strip())
    except:
        return None

def convertir_fechas(fecha_str):
    try:
        fecha_limpia = str(fecha_str).lower().replace("a. m.", "am").replace("p. m.", "pm").strip()
        fecha = pd.to_datetime(fecha_limpia, format='%d/%m/%Y %I:%M:%S %p', errors='coerce')
        return fecha if not pd.isna(fecha) else pd.to_datetime(fecha_limpia, format='%d/%m/%Y %H:%M:%S', errors='coerce')
    except:
        return pd.NaT

def procesar_datos(df):
    # Procesamiento de coordenadas
    df['Tecnico_Clean'] = df['4.Nombre del Técnico Instalador'].str.strip().str.upper()
    df['Latitud_adj'] = df['Latitud']
    df['Longitud_adj'] = df['Longitud']
    
    groups = df.groupby(['Latitud', 'Longitud'])
    for (lat, lon), group in groups:
        if len(group) > 1:
            for i, idx in enumerate(group.index[1:]):
                angle = np.random.uniform(0, 2 * np.pi)
                delta_lat = (5 / 111320) * np.cos(angle)
                delta_lon = (5 / (111320 * np.cos(np.radians(lat)))) * np.sin(angle)
                df.at[idx, 'Latitud_adj'] = lat + delta_lat
                df.at[idx, 'Longitud_adj'] = lon + delta_lon
    
    df["Latitud"] = df["Latitud"].apply(parse_coord)
    df["Longitud"] = df["Longitud"].apply(parse_coord)
    df = df.dropna(subset=["Latitud", "Longitud"])
    df = df[(df["Latitud"] > 0) & (df["Longitud"] < 0)]
    df['FechaCreacion'] = df['FechaCreacion'].apply(convertir_fechas)
    
    # Generar colores
    tecnicos = sorted(df['Tecnico_Clean'].dropna().unique())
    colores = {t: f"rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)})" 
              for t in tecnicos}
    
    return df, colores