import pandas as pd
import numpy as np

# --- Helpers ---

def time_str_to_seconds(s):
    """Convierte 'hh:mm:ss' o 'mm:ss' a segundos."""
    if pd.isna(s):
        return np.nan
    s = str(s).strip()
    if s in ["--", ""]:
        return np.nan
    parts = s.split(":")
    try:
        parts = [float(p) for p in parts]
    except ValueError:
        return np.nan

    if len(parts) == 3:
        h, m, sec = parts
        return h*3600 + m*60 + sec
    elif len(parts) == 2:
        m, sec = parts
        return m*60 + sec
    else:
        return np.nan


def get_time_of_day(dt):
    """Devuelve mañana / tarde / noche según la hora."""
    if pd.isna(dt):
        return pd.NA
    h = dt.hour
    if 6 <= h < 12:
        return "mañana"
    elif 12 <= h < 18:
        return "tarde"
    else:
        return "noche"
    
def clasificar_sesion(row):
    # --- 1) Por título ---
    title = str(row["Título"]).lower()
    keywords = ["serie", "series", "fartlek",
                "cambios", "repet", "umbral", "progresivo"]
    if any(k in title for k in keywords):
        return "quality"

    # --- 2) Por vueltas vs distancia ---
    dist = row["Distancia"]              # ya es float
    laps = row["Número de vueltas"]      # ya es int

    if dist > 0:
        ratio = laps / dist
        # en rodajes normales ≈ 1 vuelta por km
        # si hay muchas más vueltas que kms → seguro que son series
        if ratio > 1.3:                  # puedes subir/bajar este umbral
            return "quality"

    # --- 3) Tirada larga ---
    if dist >= 12:
        return "long"

    # --- 4) Resto: rodaje fácil ---
    return "easy"

def merge_close_runs_one_runner(df, max_gap_min=20):
    """
    Junta actividades del mismo corredor si están separadas por menos de max_gap_min minutos.
    Suma distancia, tiempo y desnivel y recalcula el ritmo.
    """
    df = df.sort_values("datetime").reset_index(drop=True).copy()
    merged = []
    current = None

    for _, row in df.iterrows():
        if current is None:
            current = row.copy()
            continue

        # diferencia en minutos entre esta actividad y la que está "abierta"
        time_diff = (row["datetime"] - current["datetime"]).total_seconds() / 60

        if time_diff <= max_gap_min:
            # ---- misma sesión → fusionar ----
            dur_total = current["duration_s"] + row["duration_s"]

            # medias ponderadas por duración
            if pd.notna(current["avg_hr"]) and pd.notna(row["avg_hr"]):
                current["avg_hr"] = (
                    current["avg_hr"] * current["duration_s"]
                    + row["avg_hr"] * row["duration_s"]
                ) / dur_total

            if pd.notna(current["avg_cadence"]) and pd.notna(row["avg_cadence"]):
                current["avg_cadence"] = (
                    current["avg_cadence"] * current["duration_s"]
                    + row["avg_cadence"] * row["duration_s"]
                ) / dur_total

            # sumar duración y distancia
            current["duration_s"] = dur_total
            current["distance_km"] += row["distance_km"]

            # desnivel: suma manejando posibles NaN
            if "elev_gain_m" in df.columns:
                current["elev_gain_m"] = np.nansum(
                    [current.get("elev_gain_m", np.nan),
                     row.get("elev_gain_m", np.nan)]
                )

            # máximos
            if "max_hr" in df.columns:
                current["max_hr"] = np.nanmax(
                    [current.get("max_hr", np.nan), row.get("max_hr", np.nan)]
                )
            if "max_cadence" in df.columns:
                current["max_cadence"] = np.nanmax(
                    [current.get("max_cadence", np.nan), row.get("max_cadence", np.nan)]
                )

        else:
            # cerramos sesión actual y abrimos una nueva
            merged.append(current)
            current = row.copy()

    if current is not None:
        merged.append(current)

    out = pd.DataFrame(merged)
    # recalculamos el ritmo en s/km por si ha cambiado
    out["pace_s_per_km"] = out["duration_s"] / out["distance_km"]
    return out
