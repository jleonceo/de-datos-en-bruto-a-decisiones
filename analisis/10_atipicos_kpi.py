# -*- coding: utf-8 -*-
"""
10_atipicos_kpi.py: Lo que faltaba de los bloques E (atipicos), D (descriptiva) y J (cuadro de mando).

Que calcula cada bloque, declarado en su campo `estadistico`:
  E2   atipico por z-score, frente al de rango intercuartilico que la web ya usa.
  E7   tiempo hasta la deteccion: cuanto tarda en saltar una anomalia desde que ocurre.
  E8   fatiga de alertas: cuantos avisos al mes produce cada umbral.
  E9   las tres clases de anomalia (puntual, contextual y colectiva) contadas por separado.
  E11  LOF y DBSCAN sobre las mismas ventas, comparados con el IsolationForest que ya hay.
  E6   tasa de falsos positivos, precision y exhaustividad de cuatro detectores (23/09).
  D3   forma de cada variable, con D11: media frente a mediana cuando hay cola larga (23/09).
  D4   Pareto por producto, por provincia y por venta; no por cliente, que no hay clave (23/09).
  D6   el nivel de agregacion: la misma pregunta contestada por venta, por mes y por anio,
       solo con anios completos (23/09).
  D12  el denominador olvidado: ranking de provincias por total y por venta.
  J1   KPI frente a metrica de vanidad, con los dos calculados.
  J9   el mapa por provincia, con lo que hace falta para pintarlo.

Semilla 42. Vuelca analisis/salidas/atipicos_kpi.json.
"""
import pandas as pd, numpy as np, json, os
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
CLEAN = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT = os.path.join(HERE, "salidas", "atipicos_kpi.json")
SEED = 42


def e2_zscore(df):
    x = df["importe"].values.astype(float)
    z = (x - x.mean()) / x.std(ddof=0)
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    lim_iqr = q3 + 1.5 * iqr
    marcados_z = {}
    for u in (2, 2.5, 3):
        marcados_z[str(u)] = int((abs(z) > u).sum())
    reales = set(df[df.anomalia == 1]["id_venta"])
    cazadas_z3 = len(reales & set(df[abs(z) > 3]["id_venta"]))
    cazadas_iqr = len(reales & set(df[x > lim_iqr]["id_venta"]))
    return {
        "estadistico": "ventas marcadas por z-score a tres umbrales, frente al limite de Tukey por IQR",
        "n": int(len(x)),
        "media": round(float(x.mean()), 2), "desviacion": round(float(x.std(ddof=0)), 2),
        "marcados_por_z": marcados_z,
        "limite_iqr_superior": round(float(lim_iqr), 2),
        "marcados_por_iqr": int((x > lim_iqr).sum()),
        "anomalias_reales": len(reales),
        "reales_cazadas_por_z3": cazadas_z3,
        "reales_cazadas_por_iqr": cazadas_iqr,
        "z_del_mayor": round(float(z.max()), 2),
        "lectura": "el z-score usa media y desviacion, que los propios atipicos inflan; aqui la anomalia que se escapa lo hace porque su importe es normal entre los productos caros",
    }


def e7_tiempo_deteccion(df):
    an = df[df.anomalia == 1].copy()
    if an.empty:
        return {"medido": False}
    an["fecha"] = pd.to_datetime(an["fecha"])
    d = df.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    cierre = d.groupby(d["fecha"].dt.to_period("M"))["fecha"].max()
    filas = []
    for _, r in an.iterrows():
        fin_mes = cierre[r["fecha"].to_period("M")]
        filas.append({"id": r["id_venta"], "fecha": str(r["fecha"].date()),
                      "dias_hasta_cierre_de_mes": int((fin_mes - r["fecha"]).days),
                      "motivo": r["motivo_anomalia"]})
    dias = [z["dias_hasta_cierre_de_mes"] for z in filas]
    return {
        "estadistico": "dias entre la venta anomala y el cierre del mes, que es cuando la veria un informe mensual",
        "n_anomalias": len(filas),
        "media_dias": round(float(np.mean(dias)), 1),
        "max_dias": int(max(dias)), "min_dias": int(min(dias)),
        "detalle": filas,
        "con_control_diario": 1,
        "lectura": "un control mensual tarda de media dos semanas en ver lo que un control diario ve al dia siguiente",
    }


def e8_fatiga(df):
    """Umbrales en euros, que es como se configura una alerta de verdad.

    La primera version usaba umbrales de z y salio inservible: z>1,5 y z>2 marcaban las MISMAS
    1.185 ventas, y z>2,5 y z>3 las mismas 760. El importe solo toma unos pocos valores, porque
    son ocho productos por cantidades enteras, asi que entre un umbral y el siguiente no cae
    ninguna venta. El defecto era del instrumento, no del dato.
    """
    d = df.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    meses = d["fecha"].dt.to_period("M").nunique()
    x = d["importe"].values.astype(float)
    filas = []
    for u in (5000, 8000, 10000, 15000, 20000, 30000):
        marca = x > u
        n = int(marca.sum())
        aciertos = int((marca & (d.anomalia == 1).values).sum())
        filas.append({"umbral_euros": u, "avisos": n,
                      "avisos_por_mes": round(n / meses, 1),
                      "aciertos": aciertos,
                      "precision_pct": round(100 * aciertos / n, 2) if n else None,
                      "cobertura_pct": round(100 * aciertos / int((d.anomalia == 1).sum()), 1)})
    return {
        "estadistico": "avisos al mes, precision y cobertura de cada umbral en euros",
        "meses": int(meses),
        "anomalias_reales": int((df.anomalia == 1).sum()),
        "por_umbral": filas,
        "lectura": "bajar el umbral multiplica los avisos y hunde la precision, y con muchos avisos falsos es facil dejar de mirarlos",
    }


def e9_clases(df):
    d = df.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    x = d["importe"].values.astype(float)
    q1, q3 = np.percentile(x, [25, 75])
    puntual = int((x > q3 + 1.5 * (q3 - q1)).sum())
    # contextual: pasa desapercibida en el total y se sale DENTRO de su provincia y su mes.
    # La primera version comparaba contra el producto y daba CERO, porque una venta rara para un
    # producto caro ya es rara en el total: los dos criterios miraban lo mismo.
    lim_global = q3 + 1.5 * (q3 - q1)
    cont = 0
    for _, g in d.groupby(["reg", d["fecha"].dt.to_period("Q")]):
        v = g["importe"].values.astype(float)
        if len(v) < 20:
            continue
        a, b = np.percentile(v, [25, 75])
        lim = b + 1.5 * (b - a)
        cont += int(((v > lim) & (v <= lim_global)).sum())
    # colectiva: meses cuyo total se sale de la banda, aunque ninguna venta suelta lo haga
    m = d.groupby(d["fecha"].dt.to_period("M"))["importe"].sum()
    m = m[:-1]
    lo, hi = m.mean() - 2 * m.std(ddof=1), m.mean() + 2 * m.std(ddof=1)
    colectiva = int(((m < lo) | (m > hi)).sum())
    return {
        "estadistico": "cada clase contada con el criterio que le corresponde, sobre la misma tabla",
        "puntual": puntual,
        "contextual": cont,
        "colectiva_meses": colectiva,
        "meses_analizados": int(len(m)),
        "banda_mensual": [round(float(lo), 2), round(float(hi), 2)],
        "lectura": "son tres preguntas distintas: raro a secas, raro para su grupo, y raro como racha",
    }


def e11_lof_dbscan(df):
    rng = np.random.default_rng(SEED)
    d = df.dropna(subset=["satisfaccion"])
    idx = rng.choice(len(d), 4000, replace=False)
    sub = d.iloc[idx]
    X = StandardScaler().fit_transform(sub[["importe", "cant", "satisfaccion"]].values.astype(float))
    lof = LocalOutlierFactor(n_neighbors=35, contamination=0.01)
    et_lof = lof.fit_predict(X)
    db = DBSCAN(eps=0.8, min_samples=10).fit(X)
    reales = int((sub.anomalia == 1).sum())
    return {
        "estadistico": "LOF al 1 % y DBSCAN sobre una muestra de 4.000 ventas tipificadas en tres variables",
        "n_muestra": int(len(sub)),
        "anomalias_reales_en_la_muestra": reales,
        "lof_marcadas": int((et_lof == -1).sum()),
        "lof_aciertos": int(((et_lof == -1) & (sub.anomalia == 1).values).sum()),
        "dbscan_ruido": int((db.labels_ == -1).sum()),
        "dbscan_grupos": int(len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)),
        "dbscan_aciertos": int(((db.labels_ == -1) & (sub.anomalia == 1).values).sum()),
        "lectura": "LOF mira la densidad local y DBSCAN llama ruido a lo que no cabe en ningun grupo denso",
    }


def d6_nivel_agregacion(val):
    d = val.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    # Solo anios completos: un anio a medias baja la suma anual y la media mensual sin que las ventas bajen.
    ultima = d["fecha"].max()
    anio_fin = ultima.year if (ultima.month, ultima.day) == (12, 31) else ultima.year - 1
    anio_ini = int(d["fecha"].dt.year.min())
    d = d[d["fecha"].dt.year <= anio_fin]
    por_venta = d.groupby("reg")["importe"].mean().sort_values(ascending=False)
    mensual = d.groupby(["reg", d["fecha"].dt.to_period("M")])["importe"].sum().groupby("reg").mean().sort_values(ascending=False)
    anual = d.groupby(["reg", d["fecha"].dt.year])["importe"].sum().groupby("reg").mean().sort_values(ascending=False)
    return {
        "estadistico": "la misma pregunta (que provincia va primera) respondida con tres niveles de agregacion",
        "anio_inicio": anio_ini,
        "anio_fin": int(anio_fin),
        "ventas_usadas": int(len(d)),
        "por_venta_top3": [{"reg": k, "v": round(float(v), 2)} for k, v in por_venta.head(3).items()],
        "por_mes_top3": [{"reg": k, "v": round(float(v), 2)} for k, v in mensual.head(3).items()],
        "por_anio_top3": [{"reg": k, "v": round(float(v), 2)} for k, v in anual.head(3).items()],
        "coinciden_los_tres_primeros": bool(por_venta.index[0] == mensual.index[0] == anual.index[0]),
        "lectura": "cambiar el nivel de agregacion cambia el ganador: se elige por la decision que se va a tomar",
    }


def d12_denominador(val):
    tot = val.groupby("reg")["importe"].agg(["size", "sum", "mean"])
    por_total = tot.sort_values("sum", ascending=False)
    por_venta = tot.sort_values("mean", ascending=False)
    pos_total = {r: i + 1 for i, r in enumerate(por_total.index)}
    pos_venta = {r: i + 1 for i, r in enumerate(por_venta.index)}
    saltos = sorted(((r, pos_total[r], pos_venta[r], pos_total[r] - pos_venta[r]) for r in tot.index),
                    key=lambda z: -abs(z[3]))[:5]
    return {
        "estadistico": "las mismas provincias ordenadas por facturacion total y por facturacion por venta",
        "n_provincias": int(len(tot)),
        "lider_por_total": por_total.index[0],
        "lider_por_venta": por_venta.index[0],
        "mayores_saltos": [{"reg": r, "puesto_por_total": a, "puesto_por_venta": b, "salto": abs(c)}
                           for r, a, b, c in saltos],
        "lectura": "un total premia al que tiene mas ventas; el denominador decide a quien estas llamando mejor",
    }


def d3_d11_forma(val):
    """Forma de cada variable, y el caso en que media y mediana dejan de contar lo mismo.

    Control incluido: la cantidad va de 1 a 5 casi por igual, asi que su asimetria tiene que salir
    cerca de cero. Si saliera como la del importe, el calculo estaria midiendo otra cosa.
    """
    from scipy.stats import skew, kurtosis
    filas = {}
    for col in ("importe", "precio", "cant", "satisfaccion"):
        x = val[col].dropna().values.astype(float)
        filas[col] = {"n": int(len(x)), "media": round(float(x.mean()), 2),
                      "mediana": round(float(np.median(x)), 2),
                      "asimetria": round(float(skew(x)), 3),
                      "curtosis_exceso": round(float(kurtosis(x)), 3),
                      "pct_por_debajo_de_la_media": round(100 * float((x < x.mean()).mean()), 1)}
    imp = val["importe"].values.astype(float)
    bordes = np.arange(0, 18000, 1000)
    cuenta, _ = np.histogram(imp, bins=np.append(bordes, 18000))
    orden = np.sort(imp)[::-1]
    cola = orden[: int(len(orden) * 0.10)].sum() / orden.sum()
    return {
        "estadistico": "asimetria, curtosis y media frente a mediana de cuatro variables, con el histograma del importe",
        "variables": filas,
        "histograma_importe": [{"desde": int(b), "hasta": int(b + 1000), "ventas": int(c)} for b, c in zip(bordes, cuenta)],
        "pct_facturacion_del_10pct_mayor": round(100 * float(cola), 1),
        "lectura": "con cola larga a la derecha la media se va hacia la cola y deja de describir la venta tipica",
    }


def d4_pareto(val):
    """Curva de concentracion por producto, por provincia y por venta suelta.

    El Pareto clasico se hace por cliente, y aqui no se puede: el correo no identifica a nadie
    (07_ml.py lo midio el 13/09). Se hace sobre lo que si tiene identidad.
    """
    salida = {}
    for nombre, serie in (("productos", val.groupby("prod")["importe"].sum()),
                          ("provincias", val.groupby("reg")["importe"].sum()),
                          ("ventas", val["importe"])):
        s = serie.sort_values(ascending=False).values.astype(float)
        acum = np.cumsum(s) / s.sum()
        n80 = int(np.searchsorted(acum, 0.80) + 1)
        top20 = acum[max(int(round(len(s) * 0.20)) - 1, 0)]
        curva = [{"pct_elementos": round(100 * (i + 1) / len(s), 1), "pct_facturacion": round(100 * float(a), 1)}
                 for i, a in enumerate(acum)] if len(s) <= 60 else \
                [{"pct_elementos": p, "pct_facturacion": round(100 * float(acum[int(len(s) * p / 100) - 1]), 1)}
                 for p in range(5, 101, 5)]
        salida[nombre] = {"n": int(len(s)), "n_para_80pct": n80,
                          "pct_elementos_para_80pct": round(100 * n80 / len(s), 1),
                          "pct_facturacion_del_20pct_mayor": round(100 * float(top20), 1),
                          "curva": curva}
    return {
        "estadistico": "cuanta facturacion concentra el primer 20 % de productos, de provincias y de ventas",
        **salida,
        "lectura": "el 80/20 no es una ley: por producto hay concentracion, menor que la de la regla, y por provincia la facturacion esta repartida",
    }


def e6_tasas(df):
    """Tasa de falsos positivos, precision y exhaustividad de cada detector frente a la regla.

    La verdad es la regla del catalogo, las 16 anomalias. El IsolationForest se lee de ml.json,
    que lo calcula 07_ml.py; los otros tres se recalculan aqui igual que en su pagina.
    """
    reales = df["anomalia"].values == 1
    x = df["importe"].values.astype(float)
    z = (x - x.mean()) / x.std(ddof=0)
    q1, q3 = np.percentile(x, [25, 75])
    lim = q3 + 1.5 * (q3 - q1)
    por_prod = np.zeros(len(df), dtype=bool)
    for _, g in df.groupby("prod"):
        c = g["cant"].values.astype(float)
        a, b = np.percentile(c, [25, 75])
        por_prod[g.index] = c > b + 1.5 * (b - a)
    detectores = {"iqr_global_importe": x > lim, "zscore_mayor_3": abs(z) > 3,
                  "iqr_por_producto_cantidad": por_prod}
    ml = os.path.join(HERE, "salidas", "ml.json")
    filas = []
    for nombre, m in detectores.items():
        vp = int((m & reales).sum()); fp = int((m & ~reales).sum())
        filas.append({"detector": nombre, "marcadas": int(m.sum()), "verdaderos": vp, "falsos": fp})
    if os.path.exists(ml):
        a = json.load(open(ml, encoding="utf-8"))["anomalias"]
        filas.append({"detector": "isolationforest", "marcadas": a["isolationforest_n"],
                      "verdaderos": a["anomalias_regla_cazadas"],
                      "falsos": a["marcadas_que_no_son_anomalia_de_regla"]})
    normales = int((~reales).sum()); n_reales = int(reales.sum())
    for f in filas:
        f["tasa_falsos_positivos_pct"] = round(100 * f["falsos"] / normales, 2)
        f["precision_pct"] = round(100 * f["verdaderos"] / f["marcadas"], 1) if f["marcadas"] else None
        f["exhaustividad_pct"] = round(100 * f["verdaderos"] / n_reales, 1)
    return {
        "estadistico": "tasa de falsos positivos, precision y exhaustividad de cuatro detectores contra las 16 de la regla",
        "normales": normales, "anomalias_reales": n_reales,
        "detectores": filas,
        "lectura": "una tasa de falsos positivos baja puede esconder una precision pesima cuando lo raro es muy raro",
    }


def j1_kpi(val):
    d = val.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    m = d.groupby(d["fecha"].dt.to_period("M"))
    n_ventas = m.size()
    facturacion = m["importe"].sum()
    return {
        "estadistico": "tres magnitudes mensuales, dos de vanidad y una accionable",
        "vanidad_numero_de_ventas": {"media": round(float(n_ventas[:-1].mean()), 1),
                                     "crecimiento_pct": round(100 * (n_ventas.iloc[-2] / n_ventas.iloc[0] - 1), 1)},
        "vanidad_facturacion_acumulada": round(float(facturacion.sum()), 2),
        "kpi_ticket_medio": round(float(d["importe"].mean()), 2),
        # 23/09/2026: la recurrencia se calculaba por correo y daba un 39,1 % falso; el correo lo
        # comparten personas distintas (07_ml.py, segmentacion_clientes). Sin clave no hay KPI.
        "kpi_recurrencia": None,
        "kpi_recurrencia_motivo": "no hay clave de cliente: el correo lo comparten personas distintas",
        "lectura": "el acumulado solo puede subir, asi que nunca avisa de nada; el ticket medio si, y la recurrencia lo haria con una clave de cliente",
    }


def j9_mapa(val):
    g = val.groupby("reg").agg(ventas=("id_venta", "size"), importe=("importe", "sum"),
                               ticket=("importe", "mean"), satisfaccion=("satisfaccion", "mean"))
    g = g.sort_values("importe", ascending=False)
    return {
        "estadistico": "las cuatro magnitudes por provincia que necesita un mapa coropletico",
        "n_provincias": int(len(g)),
        "provincias": [{"reg": k, "ventas": int(v.ventas), "importe": round(float(v.importe), 2),
                        "ticket": round(float(v.ticket), 2),
                        "satisfaccion": round(float(v.satisfaccion), 3)} for k, v in g.iterrows()],
        "importe_max": round(float(g.importe.max()), 2),
        "importe_min": round(float(g.importe.min()), 2),
        "lectura": "el mapa pinta 52 provincias, y lo que decide si engaña es que magnitud se pinta",
    }


def main():
    df = pd.read_csv(CLEAN, encoding="utf-8")
    val = df[df["anomalia"] == 0]
    out = {
        "semilla": SEED,
        "e2_zscore": e2_zscore(df),
        "e7_tiempo_deteccion": e7_tiempo_deteccion(df),
        "e8_fatiga_alertas": e8_fatiga(df),
        "e9_clases_de_anomalia": e9_clases(df),
        "e11_lof_dbscan": e11_lof_dbscan(df),
        "e6_tasas": e6_tasas(df),
        "d3_d11_forma": d3_d11_forma(val),
        "d4_pareto": d4_pareto(val),
        "d6_nivel_agregacion": d6_nivel_agregacion(val),
        "d12_denominador": d12_denominador(val),
        "j1_kpi_vs_vanidad": j1_kpi(val),
        "j9_mapa": j9_mapa(val),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("== ATIPICOS Y KPI ==")
    for k, v in out.items():
        if isinstance(v, dict):
            print("%-26s %s" % (k, v.get("lectura", "")[:74]))


if __name__ == "__main__":
    main()
