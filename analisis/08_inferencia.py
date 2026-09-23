# -*- coding: utf-8 -*-
"""
08_inferencia.py: Los ocho conceptos del bloque F que la web no calculaba.

Cada uno declara en su campo `estadistico` exactamente que mide, igual que 06_robustez.py, para
que la pagina no pueda afirmar mas de lo que se ha calculado:
  F5   intervalo de confianza del 95 % del ticket medio, por el metodo del percentil del bootstrap.
  F8   potencia: cuantas ventas harian falta para detectar la diferencia de ticket entre dos regiones.
  F9   paradoja de Simpson: la region que gana en el agregado y pierde producto a producto.
  F10  margen de un KPI por bootstrap, sobre la facturacion mensual media.
  F11  Bonferroni frente a Benjamini-Hochberg sobre los contrastes de provincia.
  F12  bootstrap no parametrico frente al intervalo normal, sobre la misma magnitud.
  F13  correlacion parcial entre importe y satisfaccion, controlando el producto.
  F15  emparejamiento por puntuacion de propension entre dos regiones, sobre el ticket medio.

Cada bloque tiene su propio generador derivado de la semilla 42: quitar uno no mueve el resultado
de otro. Vuelca analisis/salidas/inferencia.json.
"""
import pandas as pd, numpy as np, json, os
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
CLEAN = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT = os.path.join(HERE, "salidas", "inferencia.json")
SEED = 42
N_BOOT = 5000


def boot_media(x, n=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    return x[idx].mean(axis=1)


def f5_intervalo(val):
    x = val["importe"].values.astype(float)
    b = boot_media(x)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return {
        "estadistico": "ticket medio de una venta, con su intervalo del 95 % por percentil del bootstrap",
        "n": int(len(x)), "n_bootstrap": N_BOOT,
        "media": round(float(x.mean()), 2),
        "ic95_bajo": round(float(lo), 2), "ic95_alto": round(float(hi), 2),
        "ancho": round(float(hi - lo), 2),
        "lectura": "de cada 100 muestras como esta, unas 95 darian un intervalo que contiene el valor verdadero",
    }


def f8_potencia(val, a, b):
    xa = val[val.reg == a]["importe"].values.astype(float)
    xb = val[val.reg == b]["importe"].values.astype(float)
    s = np.sqrt((xa.var(ddof=1) + xb.var(ddof=1)) / 2)
    d = abs(xa.mean() - xb.mean()) / s
    n_necesario = int(np.ceil(2 * ((1.96 + 0.84) / d) ** 2)) if d > 0 else None
    t, p = stats.ttest_ind(xa, xb, equal_var=False)
    return {
        "estadistico": "tamano de muestra por grupo para detectar la diferencia observada con 80 % de potencia y 5 % de error",
        "region_a": a, "region_b": b,
        "n_a": int(len(xa)), "n_b": int(len(xb)),
        "media_a": round(float(xa.mean()), 2), "media_b": round(float(xb.mean()), 2),
        "d_de_cohen": round(float(d), 4),
        "n_por_grupo_necesario": n_necesario,
        "p_valor_t": round(float(p), 4),
        "alcanza": bool(len(xa) >= (n_necesario or 0) and len(xb) >= (n_necesario or 0)),
        "lectura": "si el n necesario supera al que hay, el estudio no podia detectar ese efecto aunque fuera real",
    }


def f9_simpson(val):
    tot = val.groupby("reg")["importe"].agg(["size", "mean"])
    tot = tot[tot["size"] >= 200].sort_values("mean", ascending=False)
    alto, bajo = tot.index[0], tot.index[-1]
    g = val.groupby(["reg", "prod"])["importe"].agg(["size", "mean"])
    filas, invertidos = [], 0
    for pr in sorted(val["prod"].unique()):
        try:
            a, b = g.loc[(alto, pr)], g.loc[(bajo, pr)]
        except KeyError:
            continue
        se_invierte = bool(a["mean"] < b["mean"])
        invertidos += se_invierte
        filas.append({"producto": pr, "n_alto": int(a["size"]), "media_alto": round(float(a["mean"]), 1),
                      "n_bajo": int(b["size"]), "media_bajo": round(float(b["mean"]), 1),
                      "se_invierte": se_invierte})
    caro = val.groupby("prod")["importe"].mean().idxmax()
    mix = val.assign(c=(val["prod"] == caro)).groupby("reg")["c"].mean()
    return {
        "estadistico": "ticket medio por region en el agregado, frente al mismo ticket dentro de cada producto",
        "region_agregado_alto": alto, "media_alto": round(float(tot.loc[alto, "mean"]), 2),
        "region_agregado_bajo": bajo, "media_bajo": round(float(tot.loc[bajo, "mean"]), 2),
        "brecha_pct": round(100 * (tot.loc[alto, "mean"] / tot.loc[bajo, "mean"] - 1), 1),
        "detalle_por_producto": filas,
        "productos_invertidos": invertidos, "productos_comparados": len(filas),
        "producto_caro": caro,
        "peso_producto_caro_alto_pct": round(100 * float(mix[alto]), 1),
        "peso_producto_caro_bajo_pct": round(100 * float(mix[bajo]), 1),
        "hay_paradoja": bool(invertidos > len(filas) / 2),
        "lectura": "la region que gana en el total pierde producto a producto: lo que cambia es la mezcla y no el rendimiento",
    }


def f10_kpi(val):
    m = val.groupby("anio_mes")["importe"].sum()
    ultimo = m.index.max()
    x = m[m.index != ultimo].values.astype(float)
    b = boot_media(x, seed=SEED + 1)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return {
        "estadistico": "facturacion mensual media con su margen del 95 % por bootstrap, sobre meses completos",
        "n_meses": int(len(x)), "n_bootstrap": N_BOOT,
        "media": round(float(x.mean()), 2),
        "ic95_bajo": round(float(lo), 2), "ic95_alto": round(float(hi), 2),
        "margen_pct": round(100 * (hi - lo) / 2 / x.mean(), 2),
        "lectura": "un KPI sin margen invita a leer como caida lo que cabe dentro de su propia variacion",
    }


def f11_multiples(val):
    sat = val.dropna(subset=["satisfaccion"])
    glob = sat["satisfaccion"].mean()
    filas = []
    for r, g in sat.groupby("reg"):
        if len(g) < 30:
            continue
        t, p = stats.ttest_1samp(g["satisfaccion"].values, glob)
        filas.append({"region": r, "n": int(len(g)), "media": round(float(g["satisfaccion"].mean()), 3),
                      "p": float(p)})
    filas.sort(key=lambda z: z["p"])
    k = len(filas)
    alfa = 0.05
    bonf = alfa / k
    sig_crudo = sum(1 for z in filas if z["p"] < alfa)
    sig_bonf = sum(1 for z in filas if z["p"] < bonf)
    sig_bh, umbral_bh = 0, 0.0
    for i, z in enumerate(filas, 1):
        if z["p"] <= i / k * alfa:
            sig_bh, umbral_bh = i, i / k * alfa
    for z in filas:
        z["p"] = round(z["p"], 4)
    return {
        "estadistico": "cada provincia contra la satisfaccion media global, con los tres umbrales sobre los mismos p",
        "n_contrastes": k, "alfa": alfa,
        "umbral_bonferroni": round(bonf, 5), "umbral_bh_mayor": round(umbral_bh, 5),
        "significativos_sin_corregir": sig_crudo,
        "significativos_bonferroni": sig_bonf,
        "significativos_bh": sig_bh,
        "esperados_por_azar": round(alfa * k, 1),
        "top5": filas[:5],
        "lectura": "Bonferroni controla la probabilidad de que haya algun falso positivo; BH controla que la proporcion de falsos entre los aceptados no pase del 5 %",
    }


def f12_dos_bootstrap(val):
    x = val["importe"].values.astype(float)
    b = boot_media(x, seed=SEED + 2)
    lo_np, hi_np = np.percentile(b, [2.5, 97.5])
    se = x.std(ddof=1) / np.sqrt(len(x))
    lo_p, hi_p = x.mean() - 1.96 * se, x.mean() + 1.96 * se
    return {
        "estadistico": "el mismo ticket medio por dos caminos: percentil del bootstrap y formula normal",
        "media": round(float(x.mean()), 2),
        "no_parametrico": {"bajo": round(float(lo_np), 2), "alto": round(float(hi_np), 2),
                           "ancho": round(float(hi_np - lo_np), 2)},
        "parametrico_normal": {"bajo": round(float(lo_p), 2), "alto": round(float(hi_p), 2),
                               "ancho": round(float(hi_p - lo_p), 2)},
        "asimetria_de_la_variable": round(float(stats.skew(x)), 3),
        "diferencia_de_ancho_pct": round(100 * ((hi_np - lo_np) / (hi_p - lo_p) - 1), 2),
        "lectura": "con muestras grandes los dos intervalos coinciden aunque la variable sea muy asimetrica, porque lo que tiene que ser normal es la media",
    }


def f13_parcial(val):
    d = val.dropna(subset=["satisfaccion"])
    x, y = d["importe"].values.astype(float), d["satisfaccion"].values.astype(float)
    r_bruta, p_bruta = stats.pearsonr(x, y)
    dm = d.groupby("prod")[["importe", "satisfaccion"]].transform("mean")
    rx, ry = x - dm["importe"].values, y - dm["satisfaccion"].values
    r_par, p_par = stats.pearsonr(rx, ry)
    return {
        "estadistico": "Pearson entre importe y satisfaccion, antes y despues de restar la media de su producto",
        "n": int(len(d)),
        "r_bruta": round(float(r_bruta), 4), "p_bruta": round(float(p_bruta), 4),
        "r_parcial_controlando_producto": round(float(r_par), 4), "p_parcial": round(float(p_par), 4),
        "variable_controlada": "producto",
        "lectura": "si la correlacion cambia al controlar el producto, el producto la estaba moviendo; si sigue sin ser significativa, tampoco hay relacion dentro de cada producto",
    }


def f15_propension(val):
    tot = val.groupby("reg")["importe"].agg(["size", "mean"])
    tot = tot[tot["size"] >= 200].sort_values("mean", ascending=False)
    a, b = tot.index[0], tot.index[-1]
    d = val[val.reg.isin([a, b])].copy()
    bruto = float(d[d.reg == a]["importe"].mean() - d[d.reg == b]["importe"].mean())
    rng = np.random.default_rng(SEED + 3)
    pares, dif = 0, []
    for pr, g in d.groupby("prod"):
        ga = g[g.reg == a]["importe"].values.astype(float)
        gb = g[g.reg == b]["importe"].values.astype(float)
        n = min(len(ga), len(gb))
        if n == 0:
            continue
        sa = rng.choice(ga, n, replace=False)
        sb = rng.choice(gb, n, replace=False)
        pares += n
        dif.append(float((sa - sb).sum()))
    emparejado = sum(dif) / pares if pares else None
    return {
        "estadistico": "diferencia de ticket medio entre dos regiones, cruda y emparejando por producto",
        "region_a": a, "region_b": b,
        "diferencia_bruta": round(bruto, 2),
        "diferencia_emparejada": round(emparejado, 2) if emparejado is not None else None,
        "pares_formados": pares,
        "reduccion_pct": round(100 * (1 - abs(emparejado) / abs(bruto)), 1) if emparejado else None,
        "variable_de_emparejamiento": "producto",
        "lectura": "comparar solo ventas del mismo producto quita de la diferencia lo que era mezcla",
    }


def main():
    df = pd.read_csv(CLEAN, encoding="utf-8")
    val = df[df["anomalia"] == 0]
    tot = val.groupby("reg")["importe"].agg(["size", "mean"])
    tot = tot[tot["size"] >= 200].sort_values("mean", ascending=False)
    out = {
        "semilla": SEED, "n_bootstrap": N_BOOT,
        "base": "ventas validas (sin las 16 anomalias)",
        "generador": "uno por bloque, derivado de la semilla 42",
        "f5_intervalo_confianza": f5_intervalo(val),
        "f8_potencia": f8_potencia(val, tot.index[0], tot.index[-1]),
        "f9_simpson": f9_simpson(val),
        "f10_margen_kpi": f10_kpi(val),
        "f11_comparaciones_multiples": f11_multiples(val),
        "f12_bootstrap_vs_normal": f12_dos_bootstrap(val),
        "f13_correlacion_parcial": f13_parcial(val),
        "f15_emparejamiento": f15_propension(val),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("== INFERENCIA ==")
    for k, v in out.items():
        if isinstance(v, dict):
            print("%-32s %s" % (k, v.get("lectura", "")[:72]))


if __name__ == "__main__":
    main()
