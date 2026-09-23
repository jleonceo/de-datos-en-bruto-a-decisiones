# -*- coding: utf-8 -*-
"""
verificar_correcciones.py - banco de las correcciones del 13/09/2026.

POR QUE EXISTE
La web se declaro "COMPLETO y VERIFICADO" el 01/07 con una comprobacion de sumas, y tenia 16 ventas
anomalas dadas por legitimas, una P1 medida con otro estadistico, emails con tildes, una clave de
cliente que mezcla personas y un fichero publico con k=1. Este banco comprueba cada defecto de
aquella revision, la matriz del encargo y, desde el 23/09/2026, las lecturas de los JSON que la
revision completa de la web encontro falsas (C16 a C18).

COMO SE USA
    python verificar_correcciones.py                  # sobre esta carpeta Resultado
    python verificar_correcciones.py --raiz <ruta>    # sobre otra copia (control negativo)

Lee ficheros; no ejecuta ningun script del analisis. Sale con 0 si todo es VERDE y con 1 si hay
algun ROJO. Un fichero que falta es ROJO, nunca VERDE.

LO QUE NO PRUEBA
Que las conclusiones sean correctas estadisticamente. Eso lo contrastan un recalculo independiente
desde el fichero en bruto y un revisor que intenta refutar cada conclusion.
"""
import argparse
import hashlib
import json
import os
import re
import sys

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))


def cargar_json(raiz, nombre):
    with open(os.path.join(raiz, "analisis", "salidas", nombre), encoding="utf-8") as f:
        return json.load(f)


def leer_texto(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def pagina(raiz, nombre):
    return leer_texto(os.path.join(raiz, "web", "src", "pages", nombre))


# ---------------------------------------------------------------- casos del diagnostico

def c1(raiz):
    df = pd.read_csv(os.path.join(raiz, "data", "techsoluciones_ventas_clean.csv"), dtype=str)
    n = int(df["email"].fillna("").map(lambda e: any(ord(ch) > 127 for ch in e)).sum())
    return n == 0, f"emails con caracter no ASCII: {n}"


def c2(raiz):
    df = pd.read_csv(os.path.join(raiz, "data", "techsoluciones_ventas_clean.csv"), dtype=str)
    if "anomalia" not in df.columns or "motivo_anomalia" not in df.columns:
        return False, "faltan las columnas anomalia / motivo_anomalia"
    marcadas = df[df["anomalia"].isin(["1", "True", "true"])]
    ids_ok = all(int(i[1:]) % 50 == 0 for i in marcadas["id_venta"])
    motivo_ok = marcadas["motivo_anomalia"].fillna("").str.strip().ne("").all()
    ok = len(marcadas) == 16 and ids_ok and bool(motivo_ok)
    return ok, f"marcadas={len(marcadas)} ids_multiplo_50={ids_ok} motivo_relleno={bool(motivo_ok)}"


def c3(raiz):
    p1 = cargar_json(raiz, "eda.json")["p1_mes_mayores_ventas"]
    ok = p1.get("anio_mes_top") == "2023-10" and p1.get("facturacion") == 709580.0
    return ok, f"anio_mes_top={p1.get('anio_mes_top')} facturacion={p1.get('facturacion')}"


def c4(raiz):
    p1 = cargar_json(raiz, "eda.json")["p1_mes_mayores_ventas"]
    base = str(p1.get("base", ""))
    ok = p1.get("mes_calendario_top_media") == 8 and "meses completos" in base and "sin anomal" in base
    return ok, f"mes_calendario_top_media={p1.get('mes_calendario_top_media')} base='{base}'"


def c5(raiz):
    r = cargar_json(raiz, "robustez.json")["p1_estacionalidad"]
    est = str(r.get("estadistico", ""))
    p = r.get("p_valor_permutacion")
    ok = "facturacion" in est and isinstance(p, (int, float)) and p > 0.05
    return ok, f"estadistico='{est}' p={p}"


def c6(raiz):
    ruta = os.path.join(raiz, "data", "techsoluciones_ventas_publico.csv")
    if not os.path.exists(ruta):
        return False, "no existe data/techsoluciones_ventas_publico.csv"
    df = pd.read_csv(ruta, dtype=str)
    prohibidas = [c for c in ["fecha", "anio_mes", "mes", "trimestre", "email_masc", "telefono_masc"] if c in df.columns]
    pub = cargar_json(raiz, "anonimizacion.json").get("publico", {})
    qi = pub.get("qi", [])
    if not qi or any(c not in df.columns for c in qi):
        return False, f"qi declarado {qi} no esta entero en el CSV publico"
    k_real = int(df.groupby(qi).size().min())
    ok = not prohibidas and pub.get("k_min", 0) >= 5 and k_real == pub.get("k_min")
    return ok, f"prohibidas={prohibidas} k_declarado={pub.get('k_min')} k_recalculado={k_real}"


def c7(raiz):
    # 13/09, tras la revision: la clave de persona es nombre + telefono, porque el nombre tiene
    # homonimos. El numero esperado se recalcula del CSV limpio en vez de fijarse a mano.
    df = pd.read_csv(os.path.join(raiz, "data", "techsoluciones_ventas_anon.csv"), dtype=str)
    limpio = pd.read_csv(os.path.join(raiz, "data", "techsoluciones_ventas_clean.csv"), dtype=str)
    esperado = limpio.groupby(["nombre_completo", "telefono"]).ngroups
    primero = df["cliente_id"].iloc[0]
    n = df["cliente_id"].nunique()
    return primero != "CLI-00000" and n == esperado, f"primer cliente_id={primero} distintos={n} personas={esperado}"


def c8(raiz):
    ml = cargar_json(raiz, "ml.json")
    seg = ml.get("segmentacion_clientes", {})
    ok = "segmentacion_rfm" not in ml and seg.get("viable") is False and "pct_una_compra_por_nombre" in seg
    return ok, f"rfm_presente={'segmentacion_rfm' in ml} viable={seg.get('viable')}"


FRASES_PROHIBIDAS = [
    "pedidos grandes legítimos", "53 patrones", "escéptico intenta refutar", "el riesgo cae a cero",
    "p = 0,57", "r ≈ 0,01", "dos métodos independientes",
    # 23/09/2026, revision completa de la web
    "se debía a la mezcla", "y sus cuartiles", "Tres modelos",
    "Ninguna provincia tiene una satisfacción distinta", "estaba enmascarando algo",
]


def c9(raiz):
    base = os.path.join(raiz, "web", "src")
    hallazgos = []
    for d, _, fs in os.walk(base):
        for f in fs:
            if f.endswith((".astro", ".js")):
                t = leer_texto(os.path.join(d, f))
                for fr in FRASES_PROHIBIDAS:
                    if fr in t:
                        hallazgos.append(f"{f}: '{fr}'")
    return not hallazgos, "; ".join(hallazgos) if hallazgos else "ninguna frase prohibida"


def c10(raiz):
    sal = os.path.join(raiz, "analisis", "salidas")
    web = os.path.join(raiz, "web", "src", "data")
    nombres = sorted(f for f in os.listdir(sal) if f.endswith(".json"))
    h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
    distintos = [n for n in nombres if not os.path.exists(os.path.join(web, n)) or h(os.path.join(sal, n)) != h(os.path.join(web, n))]
    return not distintos, f"{len(nombres)} JSON; distintos o ausentes en la web: {distintos}"


def c11(raiz):
    d = cargar_json(raiz, "diccionario.json")
    texto = json.dumps(d, ensure_ascii=False)
    campos = {c["campo"] for c in d.get("campos", [])}
    malas = [fr for fr in ["Eliminados 914 espacios", "coherente por producto"] if fr in texto]
    faltan = [c for c in ["anomalia", "motivo_anomalia"] if c not in campos]
    return not malas and not faltan, f"frases viejas={malas} campos que faltan={faltan}"


def c12(raiz):
    k = cargar_json(raiz, "eda.json")["kpis"]
    esperado = {"crecimiento_2019_2025_pct": -1.31, "satisfaccion_media": 5.5,
                "facturacion_registrada": 48868140.0, "facturacion_valida": 48069780.0}
    fallos = {c: k.get(c) for c, v in esperado.items() if k.get(c) != v}
    return not fallos, f"distintos de lo esperado: {fallos}" if fallos else "los cuatro KPI cuadran"


def c13(raiz):
    a = cargar_json(raiz, "eda.json").get("anomalias", {})
    ok = a.get("n") == 16 and a.get("importe_total") == 798360.0
    return ok, f"n={a.get('n')} importe_total={a.get('importe_total')}"


def c14(raiz):
    m = cargar_json(raiz, "eda.json").get("mapa_calor_provincia_anio", {})
    return len(m) == 52, f"provincias en el mapa de calor: {len(m)}"


# ---------------------------------------------------------------- matriz del encargo (C15)

def _clave(raiz, fichero, *ruta):
    try:
        v = cargar_json(raiz, fichero)
        for r in ruta:
            v = v[r]
        return v not in (None, "", [], {})
    except (KeyError, TypeError, FileNotFoundError):
        return False


def _texto_en(raiz, nombre_pagina, fragmento):
    try:
        return fragmento in pagina(raiz, nombre_pagina)
    except FileNotFoundError:
        return False


def _pasos_etl(raiz, *pasos):
    try:
        hechos = {t["paso"] for t in cargar_json(raiz, "etl_log.json")["transformaciones"]}
        return all(p in hechos for p in pasos)
    except (KeyError, FileNotFoundError):
        return False


def _diccionario_completo(raiz):
    try:
        campos = cargar_json(raiz, "diccionario.json")["campos"]
    except (KeyError, FileNotFoundError):
        return False
    return all(c.get("campo") and c.get("tipo") and c.get("descripcion")
               and (c.get("valores_posibles") or c.get("rango") or c.get("ejemplos") or c.get("formato"))
               for c in campos)


def _pii_marcada(raiz):
    try:
        return sum(str(c.get("pii", "")).startswith("SI") for c in cargar_json(raiz, "diccionario.json")["campos"]) >= 3
    except (KeyError, FileNotFoundError):
        return False


REQUISITOS = [
    ("A · fechas, numeros y categorias estandarizados",
     lambda r: _pasos_etl(r, "fechas_estandarizadas_ISO", "producto_canonicalizado", "region_canonicalizada")),
    ("A · duplicados y ausentes tratados",
     lambda r: _pasos_etl(r, "duplicados_exactos_eliminados", "satisfaccion_normalizada")),
    ("A · PII identificada", _pii_marcada),
    ("A · diccionario con nombre, tipo, descripcion y valores", _diccionario_completo),
    ("B · k-anonimidad o l-diversidad planteada",
     lambda r: _clave(r, "anonimizacion.json", "publico", "k_min") or _clave(r, "anonimizacion.json", "k_anonimidad")),
    ("B · pseudonimizacion con IDs aleatorios",
     lambda r: _clave(r, "anonimizacion.json", "interno", "pseudonimo_aleatorio")),
    ("C · media, mediana y desviacion", lambda r: _clave(r, "eda.json", "descriptivos", "importe", "desv")),
    ("C · atipicos identificados", lambda r: _clave(r, "eda.json", "atipicos")),
    ("C · deteccion automatica de anomalias", lambda r: _clave(r, "ml.json", "anomalias", "isolationforest_n")),
    ("C · anomalias documentadas con causas propuestas", lambda r: _clave(r, "eda.json", "anomalias", "hipotesis")),
    ("D · tendencia de ventas por mes",
     lambda r: _clave(r, "eda.json", "ventas_por_anio_mes") and _texto_en(r, "series.astro", "LineChart")),
    ("D · mapa de calor o geografico",
     lambda r: _clave(r, "eda.json", "mapa_calor_provincia_anio") and _texto_en(r, "cuadro-mando.astro", "Heatmap")),
    ("D · KPI de crecimiento de ventas", lambda r: _texto_en(r, "cuadro-mando.astro", "crecimiento_2019_2025_pct")),
    ("D · KPI de satisfaccion del cliente", lambda r: _texto_en(r, "cuadro-mando.astro", "satisfaccion_media")),
    ("D · alertas visuales de anomalias", lambda r: _texto_en(r, "cuadro-mando.astro", "anomalias.lista")),
    ("D · P1 mes con mayores ventas",
     lambda r: _clave(r, "eda.json", "p1_mes_mayores_ventas") and _texto_en(r, "pregunta-mes.astro", "p1")),
    ("D · P2 region con mayor crecimiento en satisfaccion",
     lambda r: _clave(r, "eda.json", "p2_region_crecimiento_satisfaccion") and _texto_en(r, "pregunta-region.astro", "p2")),
    ("D · P3 correlacion ventas y satisfaccion",
     lambda r: _clave(r, "eda.json", "p3_correlacion_ventas_satisfaccion") and _texto_en(r, "pregunta-correlacion.astro", "p3")),
    ("mision · informe tecnico profesional",
     lambda r: os.path.exists(os.path.join(r, "INFORME_TECNICO.md"))),
]


def c15(raiz):
    sin_evidencia = [nombre for nombre, prueba in REQUISITOS if not prueba(raiz)]
    return not sin_evidencia, (f"{len(REQUISITOS)} requisitos; sin evidencia ({len(sin_evidencia)}): "
                               + " | ".join(sin_evidencia) if sin_evidencia else f"{len(REQUISITOS)} requisitos con evidencia")


# ---------------------------------------------------------------- revision completa del 23/09 (C16-C18)

def c16(raiz):
    # Los correos corregidos se cuentan una vez aunque tengan espacio y tilde. Se recalcula desde el
    # bruto con la biblioteca estandar: primera fila de cada id_venta, como hace la limpieza.
    import csv
    bruto = os.path.join(os.path.dirname(raiz), "techsoluciones_ventas_dirty.csv")
    vistos, esperado = set(), 0
    with open(bruto, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["id_venta"] in vistos:
                continue
            vistos.add(fila["id_venta"])
            e = fila["email"]
            esperado += (" " in e) or not e.isascii()
    t = {x["paso"]: x for x in cargar_json(raiz, "etl_log.json")["transformaciones"]}
    antes = t["email_normalizado"]["antes"]
    return antes == esperado, f"correos corregidos en el registro={antes} recalculados={esperado}"


LECTURAS_FALSAS = [
    "se tapan a si mismos", "se cumple por producto", "95 darian una media dentro",
    "dejan de coincidir", "hay historia suficiente", "duda en una parte", "70 EUR",
    "no sesga el resultado", "ni un falso positivo", "casi nunca es un buen modelo",
    "el equipo deja de mirarlos",
]


def c17(raiz):
    hallazgos = []
    for nombre in sorted(os.listdir(os.path.join(raiz, "analisis", "salidas"))):
        if nombre.endswith(".json"):
            t = leer_texto(os.path.join(raiz, "analisis", "salidas", nombre))
            hallazgos += [f"{nombre}: '{fr}'" for fr in LECTURAS_FALSAS if fr in t]
    return not hallazgos, "; ".join(hallazgos) if hallazgos else "ninguna lectura falsa"


def c18(raiz):
    d = cargar_json(raiz, "segmentacion.json")["h12_dimensionalidad"]
    c = [x["contraste"] for x in d["por_dimension"]]
    esperado = round(100 * (1 - c[-1] / max(c)), 1)
    return d["caida_contraste"] == esperado, f"caida declarada={d['caida_contraste']} desde el maximo={esperado}"


# ---------------------------------------------------------------- publicacion del 23/09 (C19)
# Los JSON van al repositorio publico. Ninguno puede llevar valores de los identificadores directos
# (nombre, correo, telefono), ni siquiera como ejemplo o como los mas repetidos.
IDENTIFICADORES = ("nombre_completo", "email", "telefono")


def c19(raiz):
    hallazgos = []
    sal = os.path.join(raiz, "analisis", "salidas")
    for nombre in sorted(os.listdir(sal)):
        if nombre.endswith(".json"):
            t = leer_texto(os.path.join(sal, nombre))
            n_correo = len(re.findall(r"[\w.+-]+@[\w-]+\.\w+", t))
            n_tel = len(re.findall(r"\b[6-9]\d{8}\b", t))
            if n_correo or n_tel:
                hallazgos.append(f"{nombre}: {n_correo} correos, {n_tel} telefonos")
    perf = cargar_json(raiz, "perfilado.json")["campos"]
    hallazgos += [f"perfilado.{c}.top5" for c in IDENTIFICADORES if "top5" in perf.get(c, {})]
    dic = cargar_json(raiz, "diccionario.json")["campos"]
    hallazgos += [f"diccionario.{c['campo']}.ejemplos" for c in dic
                  if c["campo"] in IDENTIFICADORES and "ejemplos" in c]
    return not hallazgos, "; ".join(hallazgos) if hallazgos else "ningun identificador en los JSON"


CASOS = [("C1", c1), ("C2", c2), ("C3", c3), ("C4", c4), ("C5", c5), ("C6", c6), ("C7", c7), ("C8", c8),
         ("C9", c9), ("C10", c10), ("C11", c11), ("C12", c12), ("C13", c13), ("C14", c14), ("C15", c15),
         ("C16", c16), ("C17", c17), ("C18", c18), ("C19", c19)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=os.path.dirname(AQUI))
    raiz = ap.parse_args().raiz
    print(f"Banco de correcciones sobre: {raiz}")
    rojos = 0
    for nombre, caso in CASOS:
        try:
            ok, detalle = caso(raiz)
        except Exception as e:  # un fichero que falta o una clave que no existe es ROJO
            ok, detalle = False, f"no se pudo comprobar: {type(e).__name__}: {e}"
        rojos += not ok
        print(f"  {'VERDE' if ok else 'ROJO '}  {nombre}  {detalle}")
    print(f"{rojos} ROJO · {len(CASOS) - rojos} VERDE")
    sys.exit(1 if rojos else 0)


if __name__ == "__main__":
    main()
