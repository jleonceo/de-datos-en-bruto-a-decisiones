# -*- coding: utf-8 -*-
"""
05_eda.py: Analisis exploratorio, anomalias, las 3 preguntas del PDF y el cuadro de mando (Tareas C/D).
Solo LECTURA del CSV limpio. Vuelca analisis/salidas/eda.json (numeros listos para la web).

Dos bases, y cada bloque dice cual usa:
  - registrada: las 20.000 ventas tal como estan en el fichero
  - valida:     las 19.984 sin las 16 anomalias que marca el ETL (paso 11)
El analisis va sobre la base valida. Los agregados por mes del anio usan solo meses completos
(2026-05 esta a medias), porque sumar anios desiguales favorece a enero-mayo, que tienen uno mas.
"""
import pandas as pd, numpy as np, json, os
from scipy import stats

HERE = os.path.dirname(__file__)
CLEAN = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT = os.path.join(HERE, "salidas", "eda.json")

def r2(x):
    try: return round(float(x), 2)
    except (TypeError, ValueError): return None

def grubbs_critico(n, alfa=0.05):
    """Valor critico del test de Grubbs de dos colas: por encima, el maximo es un atipico."""
    t = stats.t.ppf(1 - alfa / (2 * n), n - 2)
    return (n - 1) / np.sqrt(n) * np.sqrt(t * t / (n - 2 + t * t))

def corr(x, y, metodo):
    m = x.notna() & y.notna()
    f = stats.pearsonr if metodo == "pearson" else stats.spearmanr
    res = f(x[m].astype(float), y[m].astype(float))
    return {"r": round(float(res[0]), 4), "p": round(float(res[1]), 4), "n": int(m.sum()), "metodo": metodo}

def main():
    df = pd.read_csv(CLEAN, encoding="utf-8")
    val = df[df["anomalia"] == 0].copy()
    ultimo_am = df["anio_mes"].max()
    out = {"n": int(len(df)), "n_validas": int(len(val)),
           "base": "valida (sin las 16 anomalias) salvo donde se diga registrada"}

    # ---------- Descriptivos (validas) ----------
    def desc(s):
        s = s.dropna()
        return {"n": int(s.count()), "media": r2(s.mean()), "mediana": r2(s.median()),
                "desv": r2(s.std()), "min": r2(s.min()), "max": r2(s.max()),
                "q1": r2(s.quantile(.25)), "q3": r2(s.quantile(.75))}
    out["descriptivos"] = {v: desc(val[v]) for v in ["importe", "cant", "precio", "satisfaccion"]}

    # ---------- Series temporales (validas) ----------
    por_anio = val.groupby("anio")["importe"].agg(["sum", "count", "mean"])
    out["ventas_por_anio"] = {int(k): {"facturacion": r2(v["sum"]), "n": int(v["count"]),
                                       "ticket_medio": r2(v["mean"])}
                              for k, v in por_anio.iterrows()}
    por_am = val.groupby("anio_mes")["importe"].sum().round(2)
    out["ventas_por_anio_mes"] = {k: r2(v) for k, v in por_am.items()}
    completos = por_am[por_am.index != ultimo_am]
    mes_de = pd.Series([int(k[5:]) for k in completos.index], index=completos.index)
    por_mes = completos.groupby(mes_de).agg(["sum", "mean", "count"])
    out["estacionalidad_mes"] = {int(k): {"facturacion_meses_completos": r2(v["sum"]),
                                          "media_mensual": r2(v["mean"]), "n_meses": int(v["count"])}
                                 for k, v in por_mes.iterrows()}

    # ---------- KPIs ----------
    fact_anio = val.groupby("anio")["importe"].sum()
    anios_completos = [a for a in fact_anio.index if a < int(ultimo_am[:4])]
    interanual = {int(a): r2(100 * (fact_anio[a] / fact_anio[a - 1] - 1))
                  for a in anios_completos if a - 1 in fact_anio.index}
    out["kpis"] = {
        "facturacion_registrada": r2(df["importe"].sum()),
        "facturacion_valida": r2(val["importe"].sum()),
        "n_ventas": int(len(df)),
        "n_validas": int(len(val)),
        "n_anomalias": int(df["anomalia"].sum()),
        "unidades_validas": int(val["cant"].sum()),
        "ticket_medio": r2(val["importe"].mean()),
        "satisfaccion_media": r2(val["satisfaccion"].mean()),
        "pct_satisfaccion_disponible": r2(100 * val["satisfaccion"].notna().mean()),
        "crecimiento_2019_2025_pct": r2(100 * (fact_anio[2025] / fact_anio[2019] - 1)),
        "crecimiento_interanual_pct": interanual,
        "n_regiones": int(val["reg"].nunique()),
        "n_productos": int(val["prod"].nunique()),
        "periodo": [df["fecha"].min(), df["fecha"].max()],
        "nota_2026": f"2026 llega hasta {ultimo_am}, mes incompleto; el crecimiento se mide 2019-2025",
    }

    # ---------- Por producto / categoria / region (validas) ----------
    prod = val.groupby("prod").agg(facturacion=("importe", "sum"), unidades=("cant", "sum"),
                                   n=("id_venta", "count"), precio_medio=("precio", "mean"),
                                   satisf_media=("satisfaccion", "mean")).sort_values("facturacion", ascending=False)
    out["por_producto"] = {k: {"facturacion": r2(v["facturacion"]), "unidades": int(v["unidades"]),
                               "n": int(v["n"]), "precio_medio": r2(v["precio_medio"]),
                               "satisf_media": r2(v["satisf_media"])} for k, v in prod.iterrows()}
    cat = val.groupby("cat").agg(facturacion=("importe", "sum"), n=("id_venta", "count"),
                                 ticket_medio=("importe", "mean"))
    out["por_categoria"] = {k: {"facturacion": r2(v["facturacion"]), "n": int(v["n"]),
                                "ticket_medio": r2(v["ticket_medio"])} for k, v in cat.iterrows()}
    reg = val.groupby("reg").agg(facturacion=("importe", "sum"), n=("id_venta", "count"),
                                 satisf_media=("satisfaccion", "mean")).sort_values("facturacion", ascending=False)
    out["por_region"] = {k: {"facturacion": r2(v["facturacion"]), "n": int(v["n"]),
                             "satisf_media": r2(v["satisf_media"])} for k, v in reg.iterrows()}

    # ---------- Anomalias (registrada) ----------
    precio_cat = df[df["anomalia"] == 0].groupby("prod")["precio"].agg(lambda s: s.mode().iloc[0])
    an = df[df["anomalia"] == 1].copy()
    an["precio_catalogo"] = an["prod"].map(precio_cat)
    out["anomalias"] = {
        "n": int(len(an)),
        "importe_total": r2(an["importe"].sum()),
        "pct_facturacion_registrada": r2(100 * an["importe"].sum() / df["importe"].sum()),
        "regla": "cantidad fuera de 1-5 (el 99,9 % de las ventas) o precio distinto del de catalogo de su producto",
        "por_cantidad": int(((an["cant"] < 1) | (an["cant"] > 5)).sum()),
        "por_precio": int(((an["precio"] - an["precio_catalogo"]).abs() > 0.005).sum()),
        "lista": [{"id_venta": r["id_venta"], "fecha": r["fecha"], "prod": r["prod"], "cant": int(r["cant"]),
                   "precio": r2(r["precio"]), "precio_catalogo": r2(r["precio_catalogo"]),
                   "importe": r2(r["importe"]), "motivo": r["motivo_anomalia"]} for _, r in an.iterrows()],
        "patron": "las 16 tienen id multiplo de 50; las cantidades son 41-45, o sea 40 + un valor normal de 1-5; "
                  "los precios fuera de catalogo son exactamente x2 o x3",
        "hipotesis": [
            "HIPOTESIS, no confirmada: un 4 tecleado delante de la cantidad (41-45 = 40 + 1..5).",
            "HIPOTESIS, no confirmada: precio de otra tarifa o de un pack multiplicado por 2 o por 3.",
            "HIPOTESIS, no confirmada: errores inyectados a proposito al generar el dataset, por la regularidad "
            "de los id (multiplos de 50).",
        ],
        "tratamiento": "marcadas y excluidas de los KPI; no se corrigen porque el valor real no se puede saber. "
                       "Se muestra la facturacion registrada al lado de la valida.",
    }

    # ---------- Atipicos: lo que es error y lo que no ----------
    imp = df["importe"]
    q1, q3 = imp.quantile(.25), imp.quantile(.75); iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    fuera_global = df[(imp < lo) | (imp > hi)]
    marca_prod = pd.Series(False, index=df.index)
    for _, g in df.groupby("prod"):
        a, b = g["cant"].quantile(.25), g["cant"].quantile(.75); d = b - a
        marca_prod.loc[g.index] = (g["cant"] < a - 1.5 * d) | (g["cant"] > b + 1.5 * d)
    z = (imp - imp.mean()) / imp.std()
    out["atipicos"] = {
        "iqr_global_importe": {
            "limite_inf": r2(lo), "limite_sup": r2(hi), "n": int(len(fuera_global)),
            "de_ellos_anomalias": int(fuera_global["anomalia"].sum()),
            "por_producto": {k: int(v) for k, v in fuera_global[fuera_global["anomalia"] == 0]["prod"].value_counts().items()},
            "lectura": "el IQR sobre el importe mezcla productos baratos y caros: marca como atipicas "
                       "ventas normales de los productos caros. No sirve para detectar errores en este dataset.",
        },
        "iqr_por_producto_cantidad": {
            "n": int(marca_prod.sum()),
            "coinciden_con_anomalias": int((marca_prod & (df["anomalia"] == 1)).sum()),
            "lectura": "dentro de cada producto la cantidad va de 1 a 5; el IQR por producto aisla justo las 16 ventas de 41-45.",
        },
        "zscore_importe_abs_gt3": int((z.abs() > 3).sum()),
        "zscore_de_ellos_anomalias": int(((z.abs() > 3) & (df["anomalia"] == 1)).sum()),
    }

    # ---------- PREGUNTA 1: mes con mayores ventas ----------
    mes_top_media = int(por_mes["mean"].idxmax())
    media_88 = completos.mean()
    mejor_por_anio = {}
    for anio, g in por_am.groupby(lambda k: int(k[:4])):
        mejor_por_anio[anio] = {"anio_mes": g.idxmax(), "facturacion": r2(g.max())}
    meses_anio = {int(k): int(v) for k, v in por_mes["count"].items()}
    suma_top = int(por_mes["sum"].idxmax())
    n_am = val.groupby("anio_mes").size()
    uds_am = val.groupby("anio_mes")["cant"].sum()
    out["p1_mes_mayores_ventas"] = {
        "anio_mes_top": por_am.idxmax(), "facturacion": r2(por_am.max()),
        "top_por_n_ventas": {"anio_mes": n_am.idxmax(), "n": int(n_am.max())},
        "top_por_unidades": {"anio_mes": uds_am.idxmax(), "unidades": int(uds_am.max())},
        "z_del_top_entre_meses_completos": r2((por_am.max() - completos.mean()) / completos.std()),
        "grubbs_critico_alfa_005": r2(grubbs_critico(len(completos))),
        "segundo": {"anio_mes": por_am.nlargest(2).index[1], "facturacion": r2(por_am.nlargest(2).iloc[1])},
        "mes_calendario_top_media": mes_top_media,
        "media_mes_calendario_top": r2(por_mes["mean"].max()),
        "media_de_los_meses_completos": r2(media_88),
        "pct_sobre_media": r2(100 * (por_mes["mean"].max() / media_88 - 1)),
        "n_meses_completos": int(len(completos)),
        "base": "meses completos, sin anomalias",
        "mejor_mes_por_anio": mejor_por_anio,
        "por_que_no_se_suma_por_mes": {
            "meses_por_mes_del_anio": meses_anio,
            "mes_top_si_se_suma": suma_top,
            "lectura": "enero a abril tienen un anio mas de datos que el resto (2026) y mayo lo tendria a medias; "
                       "sumando, esos meses ganan por tener mas meses, no por vender mas. Se compara la media.",
        },
    }

    # ---------- PREGUNTA 2: region con mayor crecimiento en satisfaccion (validas) ----------
    def pendientes(d):
        crec = {}
        for rname, g in d.dropna(subset=["satisfaccion"]).groupby("reg"):
            ann = g.groupby("anio")["satisfaccion"].mean()
            if len(ann) >= 3:
                slope = float(np.polyfit(ann.index.astype(float), ann.values, 1)[0])
                crec[rname] = {"slope": round(slope, 4), "primer_anio": r2(ann.iloc[0]),
                               "ultimo_anio": r2(ann.iloc[-1]), "delta": r2(ann.iloc[-1] - ann.iloc[0])}
        return dict(sorted(crec.items(), key=lambda kv: kv[1]["slope"], reverse=True))
    crec_ord = pendientes(val)
    sin26 = pendientes(val[val["anio"] < 2026])
    top_reg = next(iter(crec_ord))
    top_sin26 = next(iter(sin26))
    out["p2_region_crecimiento_satisfaccion"] = {
        "region_top": top_reg, "detalle_top": crec_ord[top_reg],
        "ranking_top5": {k: crec_ord[k] for k in list(crec_ord)[:5]},
        "peor5": {k: crec_ord[k] for k in list(crec_ord)[-5:]},
        "sensibilidad_sin_2026": {"region_top": top_sin26, "detalle_top": sin26[top_sin26],
                                  "misma_region": top_sin26 == top_reg},
        "nota": "slope = pendiente de la regresion lineal de la media anual de satisfaccion por provincia; "
                "2026 solo tiene cuatro meses y medio, por eso se repite sin 2026",
    }

    # ---------- PREGUNTA 3: correlacion ventas <-> satisfaccion (validas) ----------
    out["p3_correlacion_ventas_satisfaccion"] = {
        "importe_vs_satisfaccion_pearson": corr(val["importe"], val["satisfaccion"], "pearson"),
        "importe_vs_satisfaccion_spearman": corr(val["importe"], val["satisfaccion"], "spearman"),
        "cant_vs_satisfaccion_pearson": corr(val["cant"], val["satisfaccion"], "pearson"),
        "base": "validas con satisfaccion informada",
    }

    # ---------- Pareto (validas) ----------
    def pareto(series):
        s = series.sort_values(ascending=False)
        cum = s.cumsum() / s.sum()
        n80 = int((cum <= 0.8).sum()) + 1
        return {"n_para_80pct": n80, "de_total": int(len(s)), "pct_items": r2(100 * n80 / len(s))}
    out["extra_pareto"] = {"productos": pareto(prod["facturacion"]), "regiones": pareto(reg["facturacion"])}

    # ---------- Ausencia de satisfaccion: chi-cuadrado (validas) ----------
    falta = val["satisfaccion"].isna()
    chi = {}
    for col in ["reg", "anio", "prod", "cat"]:
        c2, p, dof, _ = stats.chi2_contingency(pd.crosstab(val[col], falta))
        chi[col] = {"chi2": r2(c2), "gl": int(dof), "p": round(float(p), 4)}
    out["ausencia_satisfaccion"] = {
        "pct_global": r2(100 * falta.mean()),
        "chi2_por_variable": chi,
        "todas_p_mayor_005": all(v["p"] > 0.05 for v in chi.values()),
        "lectura": "si ninguna variable cambia la proporcion de ausentes, la ausencia es compatible con "
                   "aleatoria (MCAR) en lo que esas variables permiten ver; no descarta que dependa de la propia nota (MNAR)",
    }

    # ---------- Mapa de calor: facturacion valida por provincia y anio ----------
    piv = val.pivot_table(index="reg", columns="anio", values="importe", aggfunc="sum", fill_value=0)
    out["mapa_calor_provincia_anio"] = {r: {int(a): r2(piv.loc[r, a]) for a in piv.columns}
                                        for r in piv.sum(axis=1).sort_values(ascending=False).index}
    out["mapa_calor_nota"] = f"facturacion valida por provincia y anio; 2026 es parcial (hasta {ultimo_am})"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    k, p1 = out["kpis"], out["p1_mes_mayores_ventas"]
    print("== EDA ==")
    print(f"Registrada {k['facturacion_registrada']:,.2f} | valida {k['facturacion_valida']:,.2f} | "
          f"validas {k['n_validas']} | ticket {k['ticket_medio']} | unidades {k['unidades_validas']} | satisf {k['satisfaccion_media']}")
    print("Crecimiento 2019-2025:", k["crecimiento_2019_2025_pct"], "| interanual:", k["crecimiento_interanual_pct"])
    print(f"Anomalias: {out['anomalias']['n']} por {out['anomalias']['importe_total']:,.2f}")
    print("P1 mes concreto:", p1["anio_mes_top"], p1["facturacion"], "| mes del anio por media:",
          p1["mes_calendario_top_media"], p1["media_mes_calendario_top"], f"(+{p1['pct_sobre_media']}%)",
          "| meses completos:", p1["n_meses_completos"], "| si se sumara:", p1["por_que_no_se_suma_por_mes"]["mes_top_si_se_suma"])
    print("P2:", top_reg, crec_ord[top_reg]["slope"], "| sin 2026:", top_sin26, sin26[top_sin26]["slope"])
    print("P3 Pearson:", out["p3_correlacion_ventas_satisfaccion"]["importe_vs_satisfaccion_pearson"])
    print("Atipicos IQR global:", out["atipicos"]["iqr_global_importe"]["n"], out["atipicos"]["iqr_global_importe"]["por_producto"],
          "| IQR por producto:", out["atipicos"]["iqr_por_producto_cantidad"])
    print("Chi2 ausencia:", chi)
    print("Mapa de calor:", len(out["mapa_calor_provincia_anio"]), "provincias")

if __name__ == "__main__":
    main()
