# -*- coding: utf-8 -*-
"""
09_segmentacion.py: El bloque H: las tecnicas de agrupamiento y de validacion de modelos.

La tabla NO tiene clave de cliente. El correo se forma con nombre y primer apellido, asi que lo
comparten personas distintas: 5.035 correos aparecen con nombres diferentes, y contando por nombre
y telefono cada persona compra una sola vez (07_ml.py, clave segmentacion_clientes). El 22/09/2026
se dio por buena la clave del correo y fue un error, corregido el 23/09.

Por eso la tabla RFM de este script se agrupa por correo solo como soporte para ENSENAR las
tecnicas (k-means, silueta, escalado, dimensionalidad, mezclas): sus grupos son correos y no
clientes, y la web lo avisa en cada pagina. Ningun resultado de aqui es una segmentacion de clientes.

Que calcula cada bloque, declarado en su campo `estadistico`:
  H1   RFM por correo seudonimizado, como ejercicio: el correo no identifica al cliente.
  H2   k-means sobre RFM, con el codo y la silueta para elegir k.
  H3   silueta de cada k, que es lo que dice si los grupos existen o se han fabricado.
  H5   particion en entrenamiento y prueba: el mismo modelo medido sobre lo que vio y lo que no (23/09).
  H7   fuga de informacion: el mismo modelo con y sin una variable que no se puede saber a tiempo.
  H8   efecto del escalado: k-means sobre las variables crudas frente a escaladas.
  H10  importancia de variables de un arbol, que es la lectura que un k-means no da.
  H12  maldicion de la dimensionalidad: como se aplanan las distancias al anadir columnas.
  H13  escalado robusto frente al estandar, con la variable de cola larga.
  H14  mezclas gaussianas frente a k-means: pertenencia con probabilidad frente a frontera rigida.

Semilla 42 en todo lo que muestrea. Vuelca analisis/salidas/segmentacion.json.
"""
import pandas as pd, numpy as np, json, os, hashlib
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, r2_score
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
CLEAN = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT = os.path.join(HERE, "salidas", "segmentacion.json")
SEED = 42
KS = [2, 3, 4, 5, 6]
MUESTRA_SIL = 4000


def tabla_rfm(val):
    d = val.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    hoy = d["fecha"].max()
    r = d.groupby("email").agg(
        R=("fecha", lambda s: (hoy - s.max()).days),
        F=("id_venta", "size"),
        M=("importe", "sum"),
    )
    # el correo sale seudonimizado; ojo: agrupa correos, no clientes (ver la cabecera)
    r.index = [hashlib.sha256(e.encode()).hexdigest()[:12] for e in r.index]
    return r, hoy


def h1_rfm(rfm, hoy):
    return {
        "estadistico": "recencia en dias, frecuencia en compras y valor acumulado por correo, que no identifica al cliente",
        "clave": "hash del correo, 12 caracteres",
        "fecha_de_corte": str(hoy.date()),
        "n_correos": int(len(rfm)),
        "correos_que_repiten": int((rfm.F >= 2).sum()),
        "pct_correos_que_repiten": round(100 * float((rfm.F >= 2).mean()), 1),
        "R": {"min": int(rfm.R.min()), "mediana": int(rfm.R.median()), "max": int(rfm.R.max())},
        "F": {"min": int(rfm.F.min()), "mediana": int(rfm.F.median()), "max": int(rfm.F.max())},
        "M": {"min": round(float(rfm.M.min()), 2), "mediana": round(float(rfm.M.median()), 2),
              "max": round(float(rfm.M.max()), 2)},
        "reparto_frecuencia": {str(k): int(v) for k, v in rfm.F.value_counts().sort_index().items()},
        "lectura": "los correos que repiten los usan personas distintas: no son clientes que vuelven, asi que no hay historia de cliente que agrupar",
    }


def h2_h3_kmeans(X, etiqueta):
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(X), min(MUESTRA_SIL, len(X)), replace=False)
    filas = []
    for k in KS:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(X)
        sil = float(silhouette_score(X[idx], km.labels_[idx]))
        filas.append({"k": k, "inercia": round(float(km.inertia_), 1), "silueta": round(sil, 4),
                      "tamanos": sorted([int(v) for v in np.bincount(km.labels_)], reverse=True)})
    mejor = max(filas, key=lambda z: z["silueta"])
    return {
        "estadistico": "inercia y silueta de k-means sobre %s, para k de 2 a 6" % etiqueta,
        "base": etiqueta, "n": int(len(X)), "muestra_silueta": int(len(idx)),
        "por_k": filas,
        "k_por_silueta": mejor["k"], "mejor_silueta": mejor["silueta"],
        "caida_inercia_2_a_6": round(100 * (1 - filas[-1]["inercia"] / filas[0]["inercia"]), 1),
        "lectura": "la inercia siempre baja al subir k, asi que sola no elige nada; la silueta si opina",
    }


def h8_escalado(rfm):
    crudo = rfm[["R", "F", "M"]].values.astype(float)
    esc = StandardScaler().fit_transform(crudo)
    out = {}
    for nombre, X in (("sin_escalar", crudo), ("escalado", esc)):
        km = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit(X)
        cen = pd.DataFrame(km.cluster_centers_, columns=["R", "F", "M"])
        if nombre == "escalado":
            cen = pd.DataFrame(StandardScaler().fit(crudo).inverse_transform(km.cluster_centers_),
                               columns=["R", "F", "M"])
        out[nombre] = {
            "tamanos": sorted([int(v) for v in np.bincount(km.labels_)], reverse=True),
            "centros": [{c: round(float(cen.iloc[i][c]), 1) for c in ("R", "F", "M")}
                        for i in range(len(cen))],
        }
    rango = {c: round(float(rfm[c].max() - rfm[c].min()), 1) for c in ("R", "F", "M")}
    return {
        "estadistico": "k=4 sobre las mismas tres variables, crudas y tipificadas",
        "rango_de_cada_variable": rango,
        "veces_que_M_aplasta_a_F": int(rango["M"] / rango["F"]),
        **out,
        "lectura": "k-means mide distancias: sin escalar, la variable de rango grande decide sola los grupos",
    }


def h13_robusto(rfm):
    m = rfm[["M"]].values.astype(float)
    est = StandardScaler().fit_transform(m).ravel()
    rob = RobustScaler().fit_transform(m).ravel()
    p99 = float(np.percentile(m, 99))
    return {
        "estadistico": "la misma variable M tipificada por media y desviacion, y por mediana e IQR",
        "asimetria": round(float(pd.Series(m.ravel()).skew()), 3),
        "estandar": {"media": round(float(est.mean()), 4), "max": round(float(est.max()), 2),
                     "pct_dentro_de_mas_menos_1": round(100 * float((abs(est) <= 1).mean()), 1)},
        "robusto": {"mediana": round(float(np.median(rob)), 4), "max": round(float(rob.max()), 2),
                    "pct_dentro_de_mas_menos_1": round(100 * float((abs(rob) <= 1).mean()), 1)},
        "valor_p99": round(p99, 2),
        "lectura": "con cola larga, el estandar deja a casi todos apinados cerca del cero y a los grandes lejisimos",
    }


def h14_mezclas(X):
    km = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit(X)
    gm = GaussianMixture(n_components=4, random_state=SEED, covariance_type="full").fit(X)
    prob = gm.predict_proba(X)
    maxp = prob.max(axis=1)
    return {
        "estadistico": "k=4 por k-means y por mezcla gaussiana, comparando la seguridad de cada asignacion",
        "kmeans_tamanos": sorted([int(v) for v in np.bincount(km.labels_)], reverse=True),
        "mezcla_tamanos": sorted([int(v) for v in np.bincount(gm.predict(X))], reverse=True),
        "pertenencia_media": round(float(maxp.mean()), 4),
        "pct_asignacion_dudosa": round(100 * float((maxp < 0.6).mean()), 1),
        "pct_asignacion_segura": round(100 * float((maxp > 0.9).mean()), 1),
        "bic": round(float(gm.bic(X)), 1),
        "lectura": "k-means asigna siempre al 100 %; la mezcla dice cuanto duda, y aqui casi no duda aunque la silueta sea baja",
    }


def h12_dimensionalidad(X):
    rng = np.random.default_rng(SEED)
    sub = X[rng.choice(len(X), 1500, replace=False)]
    filas = []
    for d in (1, 2, 3, 5, 10, 20, 50):
        Z = np.hstack([sub] + [rng.normal(size=(len(sub), 1)) for _ in range(max(0, d - sub.shape[1]))])
        Z = Z[:, :max(d, 1)]
        dif = Z[:, None, :] - Z[None, :, :]
        dist = np.sqrt((dif ** 2).sum(axis=2))
        iu = np.triu_indices(len(Z), 1)
        v = dist[iu]
        filas.append({"dimensiones": d, "dist_min": round(float(v.min()), 3),
                      "dist_max": round(float(v.max()), 3),
                      "contraste": round(float((v.max() - v.min()) / v.mean()), 3)})
    return {
        "estadistico": "contraste entre la distancia mayor y la menor, al anadir columnas de ruido",
        "n_puntos": 1500,
        "por_dimension": filas,
        "caida_contraste": round(100 * (1 - filas[-1]["contraste"] / max(x["contraste"] for x in filas)), 1),  # desde el maximo (23/09/2026)
        "lectura": "al subir la dimension, la distancia mas lejana y la mas cercana se parecen: agrupar pierde sentido",
    }


def h7_h10_fuga(val):
    """Predecir el importe de una oportunidad ANTES de cerrarla.

    Lo que se sabe de antemano es el producto, la provincia, la categoria y el mes. Cantidad y
    precio final solo se saben al firmar, asi que meterlas es fuga: el modelo saldria perfecto en
    el banco de pruebas y no serviria para nada el dia que hay que usarlo.

    La primera version de este bloque predecia el importe con cantidad y precio en las DOS ramas,
    y las dos daban R2 = 1,0000 exacto. El caso nacio en verde y no demostraba nada, porque
    importe = cantidad x precio: la fuga ya estaba en la rama que se llamaba limpia.
    """
    d = val.copy()
    ante = pd.get_dummies(d[["prod", "reg", "cat"]], drop_first=True)
    ante["mes"] = d["mes"].values
    X_ok = ante.values.astype(float)
    X_fuga = np.hstack([X_ok, d[["cant", "precio"]].values.astype(float)])
    y = d["importe"].values.astype(float)
    res = {}
    for nombre, X, cols in (("sin_fuga", X_ok, list(ante.columns)),
                            ("con_fuga", X_fuga, list(ante.columns) + ["cantidad", "precio"])):
        a, b, ya, yb = train_test_split(X, y, test_size=0.3, random_state=SEED)
        m = RandomForestRegressor(n_estimators=80, random_state=SEED, n_jobs=-1).fit(a, ya)
        res[nombre] = {"r2_prueba": round(float(r2_score(yb, m.predict(b))), 4),
                       "n_variables": int(X.shape[1])}
        imp = sorted(zip(cols, m.feature_importances_), key=lambda z: -z[1])[:5]
        res["importancia_" + nombre] = [{"variable": n, "peso": round(float(v), 4)} for n, v in imp]
    return {
        "estadistico": "R2 en prueba de un bosque que predice el importe, con y sin las dos variables que solo se saben al firmar",
        "n": int(len(d)), "particion": "70 % entrenamiento, 30 % prueba, semilla 42",
        "conocido_de_antemano": "producto, provincia, categoria y mes",
        "que_es_la_fuga": "cantidad y precio final, que no existen hasta cerrar la venta",
        **res,
        "lectura": "un R2 casi perfecto hay que revisarlo como posible fuga: aqui la respuesta se colaba por cantidad y precio",
    }


def h5_particion(val):
    """Por que se aparta una parte de los datos que el modelo no ve al entrenar.

    Se usa la satisfaccion porque 07_ml.py ya midio que no tiene senal (R2 de prueba ~ 0). Un
    bosque sin limite de profundidad la memoriza: sobre sus propios datos explica unos dos tercios. Si
    el R2 de entrenamiento no saliera muy por encima del de prueba, el caso no ensenaria nada.
    Se repite con cinco semillas de particion para ver cuanto baila la nota de prueba.
    """
    d = val.dropna(subset=["satisfaccion"]).copy()
    X = pd.get_dummies(d[["prod", "reg", "cat"]], drop_first=True)
    X["mes"] = d["mes"].values
    X["cant"] = d["cant"].values
    X = X.values.astype(float)
    y = d["satisfaccion"].values.astype(float)
    filas = []
    for semilla in (42, 7, 123, 2024, 99):
        a, b, ya, yb = train_test_split(X, y, test_size=0.2, random_state=semilla)
        m = RandomForestRegressor(n_estimators=80, random_state=SEED, n_jobs=-1).fit(a, ya)
        filas.append({"semilla_particion": semilla,
                      "r2_entrenamiento": round(float(r2_score(ya, m.predict(a))), 4),
                      "r2_prueba": round(float(r2_score(yb, m.predict(b))), 4)})
    pr = [f["r2_prueba"] for f in filas]
    return {
        "estadistico": "R2 de un bosque que predice la satisfaccion, medido sobre lo que vio y sobre lo que no vio, con cinco particiones",
        "n": int(len(d)), "n_entrenamiento": int(len(d) * 0.8), "n_prueba": int(len(d)) - int(len(d) * 0.8),
        "variables": "producto, provincia, categoria, mes y cantidad",
        "por_semilla": filas,
        "r2_prueba_min": min(pr), "r2_prueba_max": max(pr),
        "lectura": "medido sobre lo que ya vio, un modelo sin senal parece bueno; solo la parte apartada dice la verdad",
    }


def main():
    df = pd.read_csv(CLEAN, encoding="utf-8")
    val = df[df["anomalia"] == 0]
    rfm, hoy = tabla_rfm(val)
    crudo = rfm[["R", "F", "M"]].values.astype(float)
    esc = StandardScaler().fit_transform(crudo)

    out = {
        "semilla": SEED,
        "base": "ventas validas (sin las 16 anomalias), agregadas por cliente",
        "h1_rfm": h1_rfm(rfm, hoy),
        "h2_h3_kmeans": h2_h3_kmeans(esc, "RFM tipificado"),
        "h8_escalado": h8_escalado(rfm),
        "h12_dimensionalidad": h12_dimensionalidad(esc),
        "h13_escalado_robusto": h13_robusto(rfm),
        "h14_mezclas": h14_mezclas(esc),
        "h7_h10_fuga_e_importancia": h7_h10_fuga(val),
        "h5_particion": h5_particion(val),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("== SEGMENTACION ==")
    for k, v in out.items():
        if isinstance(v, dict):
            print("%-30s %s" % (k, v.get("lectura", "")[:74]))


if __name__ == "__main__":
    main()
