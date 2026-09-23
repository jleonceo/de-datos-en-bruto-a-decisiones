# -*- coding: utf-8 -*-
"""
04_anonimizacion.py: Anonimizacion de PII (Tarea B). Lee el CSV limpio y produce DOS ficheros:

  data/techsoluciones_ventas_anon.csv     USO INTERNO. Sin nombre, email ni telefono en claro:
                                          cliente_id aleatorio + email y telefono enmascarados.
                                          Conserva fecha, producto e importe, asi que NO se publica.
  data/techsoluciones_ventas_publico.csv  PUBLICABLE. Anio, provincia, satisfaccion y marca de
                                          anomalia. Sin categoria, producto, precio, cantidad ni importe por
                                          venta: cada producto tiene un precio unico, asi que cualquiera
                                          de esas columnas revela el producto y deja ventas unicas.
                                          Se suprimen las filas de grupos con menos de 5 ventas.

La k-anonimidad y la l-diversidad se miden SOBRE EL FICHERO PUBLICO releido de disco. Se declara ademas
cuanto bajaria k si se publicara el producto, que es lo que NO se hace.

cliente_id: una clave por persona = nombre_completo + telefono. El email lo comparten personas distintas
y el nombre tiene homonimos (los nombres con dos compras tienen dos telefonos distintos). Los numeros se
barajan con un generador de semilla 42 para que el orden de aparicion no delate a nadie.
"""
import pandas as pd, numpy as np, json, os

HERE = os.path.dirname(__file__)
CLEAN = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT_ANON = os.path.join(HERE, "..", "data", "techsoluciones_ventas_anon.csv")
OUT_PUB = os.path.join(HERE, "..", "data", "techsoluciones_ventas_publico.csv")
OUT_JSON = os.path.join(HERE, "salidas", "anonimizacion.json")
SEED = 42
K_OBJETIVO = 5

def mask_email(e):
    e = str(e)
    if "@" not in e: return "***"
    loc, dom = e.split("@", 1)
    return (loc[0] + "***@" + dom) if loc else "***@" + dom

def mask_tel(t):
    t = str(t)
    return (t[:2] + "****" + t[-2:]) if len(t) >= 4 else "****"

def k_anon(df, cols):
    g = df.groupby(cols).size()
    return {"qi": cols, "k_min": int(g.min()), "grupos": int(len(g)),
            "ventas_unicas": int((g == 1).sum()),
            "ventas_en_grupos_menores_de_5": int(g[g < 5].sum()),
            "pct_ventas_en_grupos_menores_de_5": round(100 * g[g < 5].sum() / len(df), 2)}

def l_div(df, cols, sens="satisfaccion"):
    g = df.dropna(subset=[sens]).groupby(cols)[sens].nunique()
    return {"qi": cols, "sensible": sens, "l_min": int(g.min()) if len(g) else None}

def main():
    df = pd.read_csv(CLEAN, encoding="utf-8", dtype={"telefono": str})

    # Pseudonimo aleatorio y estable por persona (clave = nombre + telefono)
    clave = df["nombre_completo"] + "|" + df["telefono"]
    personas = list(dict.fromkeys(clave))
    numeros = np.random.default_rng(SEED).permutation(len(personas))
    mapa = {p: f"CLI-{int(numeros[i]):05d}" for i, p in enumerate(personas)}
    df["cliente_id"] = clave.map(mapa)

    df["email_masc"] = df["email"].map(mask_email)
    df["telefono_masc"] = df["telefono"].map(mask_tel)

    cols_anon = ["id_venta", "fecha", "anio", "mes", "anio_mes", "trimestre",
                 "cliente_id", "email_masc", "telefono_masc",
                 "reg", "cat", "prod", "cant", "precio", "importe", "satisfaccion", "anomalia"]
    anon = df[cols_anon].copy()

    # Con categoria el grupo minimo baja a k=4 y l=2; sin ella, k=10 y l=5 sin suprimir nada.
    qi = ["anio", "reg"]
    cols_pub = qi + ["satisfaccion", "anomalia"]
    tam = df.groupby(qi)["id_venta"].transform("size")
    suprimidas = int((tam < K_OBJETIVO).sum())
    pub = df.loc[tam >= K_OBJETIVO, cols_pub].copy()

    os.makedirs(os.path.dirname(OUT_ANON), exist_ok=True)
    anon.to_csv(OUT_ANON, index=False, encoding="utf-8")
    pub.to_csv(OUT_PUB, index=False, encoding="utf-8")

    # Metricas medidas sobre el fichero publico, releido de disco
    pub_disco = pd.read_csv(OUT_PUB, encoding="utf-8")
    k_pub = k_anon(pub_disco, qi)
    l_pub = l_div(pub_disco, qi)
    si_cat = {**k_anon(df, qi + ["cat"]), "l_min": l_div(df, qi + ["cat"])["l_min"]}
    si_prod = k_anon(df, qi + ["cat", "prod"])
    si_prod_cant = k_anon(df, qi + ["cat", "prod", "cant"])

    out = {
        "registros": int(len(df)),
        "interno": {
            "fichero": "data/techsoluciones_ventas_anon.csv",
            "uso": "interno (analisis); conserva fecha, producto e importe y no se publica",
            "columnas": cols_anon,
            "clientes_unicos_pseudonimizados": int(df["cliente_id"].nunique()),
            "clave_cliente": "nombre_completo + telefono",
            "motivo_clave": "el email lo comparten personas distintas y el nombre tiene homonimos",
            "pseudonimo_aleatorio": True,
            "semilla": SEED,
            "tecnica": "cliente_id con numeracion barajada; email y telefono enmascarados; nombre retirado",
        },
        "publico": {
            "fichero": "data/techsoluciones_ventas_publico.csv",
            "columnas": cols_pub,
            "retiradas": ["id_venta", "fecha", "mes", "anio_mes", "trimestre", "nombre_completo", "email",
                          "telefono", "cliente_id", "cat", "prod", "cant", "precio", "importe"],
            "motivo_retirada_producto": "cada producto tiene un precio de catalogo unico: producto, precio, "
                                        "cantidad o importe por venta revelan el producto",
            "qi": qi,
            "k_objetivo": K_OBJETIVO,
            "filas_suprimidas": suprimidas,
            "pct_suprimido": round(100 * suprimidas / len(df), 2),
            "registros": int(len(pub_disco)),
            "k_min": k_pub["k_min"],
            "grupos": k_pub["grupos"],
            "l_min": l_pub["l_min"],
            "sensible": "satisfaccion",
            "cifras_de_venta": "se publican agregadas (eda.json), no por venta",
        },
        "riesgo_si_se_publicara": {
            "con_categoria": si_cat,
            "con_producto": si_prod,
            "con_producto_y_cantidad": si_prod_cant,
            "lectura": "medido sobre las 20.000 ventas: si el fichero publico llevara el producto, quien sepa "
                       "que compro alguien, en que anio y en que provincia encontraria su venta sola en su grupo "
                       "y leeria su satisfaccion. Por eso el producto no se publica por venta.",
        },
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("== ANONIMIZACION ==")
    print("Interno:", len(anon), "filas | clientes:", df["cliente_id"].nunique(),
          "| primer cliente_id:", anon["cliente_id"].iloc[0])
    print("Publico:", len(pub_disco), "filas | suprimidas:", suprimidas, "| k", qi, ":", k_pub["k_min"],
          "| l:", l_pub["l_min"], "| grupos:", k_pub["grupos"])
    print("Si se publicara el producto: k", si_prod["k_min"], "| unicas", si_prod["ventas_unicas"],
          "| en grupos <5", si_prod["pct_ventas_en_grupos_menores_de_5"], "%")
    print("Con producto y cantidad: k", si_prod_cant["k_min"], "| unicas", si_prod_cant["ventas_unicas"])

if __name__ == "__main__":
    main()
