# -*- coding: utf-8 -*-
"""
02_etl.py: Limpieza y estandarizacion (Tarea A). IDEMPOTENTE.
Lee el CSV crudo, aplica transformaciones documentadas y escribe:
  - data/techsoluciones_ventas_clean.csv   (dataset limpio, aun CON PII; uso interno)
  - analisis/salidas/etl_log.json           (log de cada transformacion, con conteos)
No imputa satisfaccion (se deja nula y se documenta). La anonimizacion es el paso 04.
"""
import pandas as pd, numpy as np, re, json, os, unicodedata
from datetime import datetime

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, "..", "..", "techsoluciones_ventas_dirty.csv")
OUT_CSV = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT_LOG = os.path.join(HERE, "salidas", "etl_log.json")

log = {"transformaciones": [], "avisos": []}
def r2f(x):
    return round(float(x), 2)
def paso(nombre, antes, despues, detalle=None):
    log["transformaciones"].append({"paso": nombre, "antes": antes, "despues": despues, "detalle": detalle})

# ---- Mapas canonicos ----
PROD_CANON = {
    "Modulo Nominas": "Módulo Nóminas",
    "Módulo Nóminas": "Módulo Nóminas",
    "Portatil Core i7": "Portátil Core i7",
    "Portátil Core i7": "Portátil Core i7",
    "Suscripcion CRM Pro": "Suscripción CRM Pro",
    "Suscripción CRM Pro": "Suscripción CRM Pro",
}
REG_CANON = {  # colapsa duplicados oficiales/tradicionales/abreviaturas -> 52 provincias
    "Gerona": "Girona",
    "Lérida": "Lleida",
    "Sta. Cruz de Tenerife": "Santa Cruz de Tenerife",
}
FECHA_FORMATOS = [
    (r"^\d{4}-\d{2}-\d{2}$", "%Y-%m-%d"),
    (r"^\d{4}/\d{2}/\d{2}$", "%Y/%m/%d"),
    (r"^\d{2}-\d{2}-\d{4}$", "%d-%m-%Y"),
    (r"^\d{2}/\d{2}/\d{2}$", "%m/%d/%y"),  # formato US con anio de 2 digitos
]
def sin_tildes(s):
    """NFKD separa la letra de su tilde; se descartan los caracteres combinantes."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))

def parse_fecha(s):
    s = str(s).strip()
    for rgx, fmt in FECHA_FORMATOS:
        if re.match(rgx, s):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                return None
    return None

def main():
    df = pd.read_csv(RAW, dtype=str, keep_default_na=False, encoding="utf-8")
    n0 = len(df)
    log["filas_crudas"] = n0

    # 1) Duplicados exactos (todas las columnas)
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    paso("duplicados_exactos_eliminados", n0, len(df), {"eliminadas": n0 - len(df)})

    # 2) Producto: canonicalizar acentos/variantes (10 -> 8)
    prod_antes = df["prod"].nunique()
    df["prod"] = df["prod"].map(lambda x: PROD_CANON.get(x, x))
    paso("producto_canonicalizado", int(prod_antes), int(df["prod"].nunique()),
         {"mapa": PROD_CANON})

    # 3) Region: colapsar variantes (55 -> 52)
    reg_antes = df["reg"].nunique()
    df["reg"] = df["reg"].map(lambda x: REG_CANON.get(x, x))
    paso("region_canonicalizada", int(reg_antes), int(df["reg"].nunique()),
         {"mapa": REG_CANON})

    # 4) Email: quitar espacios internos + minusculas + tildes (el encargo nombra las tres)
    # Un correo puede tener los dos defectos: los corregidos se cuentan una vez (23/09/2026; antes se
    # sumaban los dos conteos y 812 correos contaban doble).
    m_espacio = df["email"].str.contains(" ")
    m_tilde = ~df["email"].map(str.isascii)
    con_espacio, con_tilde = int(m_espacio.sum()), int(m_tilde.sum())
    con_los_dos = int((m_espacio & m_tilde).sum())
    df["email"] = df["email"].str.replace(" ", "", regex=False).str.lower()
    df["email"] = df["email"].map(sin_tildes)
    validez = df["email"].str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    paso("email_normalizado", int((m_espacio | m_tilde).sum()), 0,
         {"emails_con_espacio_corregidos": con_espacio,
          "emails_con_tilde_corregidos": con_tilde,
          "emails_con_los_dos_defectos": con_los_dos,
          "emails_no_ascii_tras_limpieza": int((~df["email"].map(str.isascii)).sum()),
          "emails_distintos": int(df["email"].nunique()),
          "emails_no_validos_tras_limpieza": int((~validez).sum())})

    # 5) Nombre: colapsar espacios multiples
    df["nombre_completo"] = df["nombre_completo"].str.replace(r"\s+", " ", regex=True).str.strip()

    # 6) Telefono: dejar solo digitos (ya son de 9)
    df["telefono"] = df["telefono"].str.replace(r"\D", "", regex=True)
    tel_bad = int((df["telefono"].str.len() != 9).sum())
    if tel_bad: log["avisos"].append(f"{tel_bad} telefonos con longitud != 9")

    # 7) Fechas -> ISO + derivados
    dt = df["fecha_str"].map(parse_fecha)
    nulos_fecha = int(dt.isna().sum())
    df["fecha"] = dt.map(lambda d: d.strftime("%Y-%m-%d") if d is not None else "")
    df["anio"] = dt.map(lambda d: d.year if d is not None else np.nan)
    df["mes"] = dt.map(lambda d: d.month if d is not None else np.nan)
    df["anio_mes"] = dt.map(lambda d: d.strftime("%Y-%m") if d is not None else "")
    df["trimestre"] = dt.map(lambda d: f"{d.year}-T{(d.month-1)//3+1}" if d is not None else "")
    rango = (df.loc[df["anio"].notna(), "anio"].min(), df.loc[df["anio"].notna(), "anio"].max())
    paso("fechas_estandarizadas_ISO", "4 formatos", "1 formato ISO",
         {"no_parseadas": nulos_fecha, "rango_anios": [int(rango[0]), int(rango[1])]})

    # 8) Numericos + importe
    df["cant"] = pd.to_numeric(df["cant"], errors="coerce").astype("Int64")
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
    df["importe"] = (df["cant"].astype("float") * df["precio"]).round(2)
    paso("importe_calculado", None, None, {"formula": "cant * precio"})

    # 9) Satisfaccion: numerica, NaN si vacia (NO se imputa)
    df["satisfaccion"] = pd.to_numeric(df["satisfaccion"].replace("", np.nan), errors="coerce")
    fuera = int(((df["satisfaccion"] < 1) | (df["satisfaccion"] > 10)).sum())
    paso("satisfaccion_normalizada", None, None,
         {"escala": "1-10", "nulos": int(df["satisfaccion"].isna().sum()),
          "pct_nulos": round(100*df["satisfaccion"].isna().mean(), 2),
          "fuera_de_escala": fuera, "politica": "no imputar; se analiza sobre casos disponibles"})

    # 10) Coherencia producto<->categoria
    inc = df.groupby("prod")["cat"].nunique()
    prod_multi_cat = inc[inc > 1].index.tolist()
    cat_por_prod = df.groupby("prod")["cat"].agg(lambda s: s.value_counts().idxmax()).to_dict()
    paso("coherencia_prod_categoria", None, None,
         {"productos_con_mas_de_una_categoria": prod_multi_cat,
          "categoria_dominante_por_producto": cat_por_prod})

    # 11) Anomalias: cantidad fuera del rango dominante (1-5) o precio fuera del de catalogo.
    #     Se MARCAN, no se borran ni se corrigen: el valor correcto no se puede saber.
    precio_catalogo = df.groupby("prod")["precio"].agg(lambda s: s.mode().iloc[0])
    df["precio_catalogo"] = df["prod"].map(precio_catalogo)
    fuera_cant = (df["cant"] < 1) | (df["cant"] > 5)
    fuera_precio = (df["precio"] - df["precio_catalogo"]).abs() > 0.005
    df["anomalia"] = (fuera_cant | fuera_precio).astype(int)

    def motivo(r):
        m = []
        if r["cant"] < 1 or r["cant"] > 5:
            m.append(f"cantidad {int(r['cant'])} fuera de 1-5")
        if abs(r["precio"] - r["precio_catalogo"]) > 0.005:
            m.append(f"precio x{r['precio'] / r['precio_catalogo']:.2f} del de catalogo ({r['precio_catalogo']:.2f})")
        return "; ".join(m)
    df["motivo_anomalia"] = ""
    df.loc[df["anomalia"] == 1, "motivo_anomalia"] = df[df["anomalia"] == 1].apply(motivo, axis=1)
    paso("anomalias_marcadas", len(df), int(df["anomalia"].sum()),
         {"regla": "cant fuera de 1-5 o precio distinto de la moda de precio de su producto",
          "precio_catalogo": {k: float(v) for k, v in precio_catalogo.items()},
          "por_cantidad": int(fuera_cant.sum()), "por_precio": int(fuera_precio.sum()),
          "por_ambas": int((fuera_cant & fuera_precio).sum()),
          "importe_marcado": r2f(df.loc[df["anomalia"] == 1, "importe"].sum()),
          "ids": df.loc[df["anomalia"] == 1, "id_venta"].tolist(),
          "politica": "marcar y excluir de los KPI de analisis; no borrar ni corregir"})

    # Orden de columnas para el CSV limpio
    cols = ["id_venta","fecha","anio","mes","anio_mes","trimestre",
            "nombre_completo","email","telefono","reg","cat","prod",
            "cant","precio","importe","satisfaccion","anomalia","motivo_anomalia"]
    df = df[cols]

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_LOG), exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    log["filas_limpias"] = len(df)
    log["columnas_finales"] = cols
    with open(OUT_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    # Resumen
    print("== ETL ==")
    print(f"Crudas: {n0}  ->  Limpias: {len(df)}  (dup. exactos: {n0-len(df)})")
    print(f"Productos: {prod_antes} -> {df['prod'].nunique()} | Regiones: {reg_antes} -> {df['reg'].nunique()}")
    print(f"Fechas no parseadas: {nulos_fecha} | Rango anios: {int(rango[0])}-{int(rango[1])}")
    print(f"Satisfaccion nula: {int(df['satisfaccion'].isna().sum())} ({round(100*df['satisfaccion'].isna().mean(),2)}%)")
    print(f"Importe total: {df['importe'].sum():,.2f}  | ticket medio: {df['importe'].mean():,.2f}")
    print(f"Prod multi-categoria: {prod_multi_cat if prod_multi_cat else 'ninguno (coherente)'}")
    print(f"Emails: {con_espacio} con espacio, {con_tilde} con tilde | no ASCII tras limpiar: "
          f"{int((~df['email'].map(str.isascii)).sum())} | distintos: {df['email'].nunique()}")
    print(f"Anomalias: {int(df['anomalia'].sum())} (cantidad {int(fuera_cant.sum())}, precio {int(fuera_precio.sum())}, "
          f"ambas {int((fuera_cant & fuera_precio).sum())}) por {df.loc[df['anomalia']==1,'importe'].sum():,.2f}")
    print("CSV ->", OUT_CSV)

if __name__ == "__main__":
    main()
