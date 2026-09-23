# -*- coding: utf-8 -*-
"""
06_robustez.py: ¿Los "hallazgos" son senal o ruido de muestreo? Tests de permutacion.

Cada test mide EXACTAMENTE el estadistico que la web afirma, y lo declara en el campo `estadistico`:
  P1  la mayor media de facturacion mensual por mes del anio, sobre los meses completos y sin anomalias.
      Se barajan las etiquetas de mes entre esos meses y se mira cuantas veces el mejor mes del azar
      iguala o supera al observado.
  P2  la mayor pendiente de satisfaccion media anual entre provincias, sobre ventas validas,
      con 2026 y sin 2026.
Cada test tiene su propio generador con semilla 42: anadir o quitar uno no cambia el p de otro.
Vuelca analisis/salidas/robustez.json.
"""
import pandas as pd, numpy as np, json, os

HERE = os.path.dirname(__file__)
CLEAN = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT = os.path.join(HERE, "salidas", "robustez.json")
SEED = 42
N_PERM = 2000

def max_slope_por_region(d):
    slopes = {}
    for rname, g in d.groupby("reg"):
        ann = g.groupby("anio")["satisfaccion"].mean()
        if len(ann) >= 3:
            slopes[rname] = float(np.polyfit(ann.index.astype(float), ann.values, 1)[0])
    return slopes

def test_p2(sat, etiqueta):
    rng = np.random.default_rng(SEED)
    obs = max_slope_por_region(sat)
    reg_top = max(obs, key=obs.get)
    vals = sat["satisfaccion"].values.copy()
    base = sat[["reg", "anio"]].copy()
    null_max = np.empty(N_PERM)
    for i in range(N_PERM):
        base["satisfaccion"] = rng.permutation(vals)
        null_max[i] = max(max_slope_por_region(base).values())
    p = float((null_max >= obs[reg_top]).mean())
    return {
        "base": etiqueta,
        "estadistico": "maxima pendiente de la satisfaccion media anual entre provincias",
        "region_observada": reg_top,
        "slope_observado_max": round(obs[reg_top], 4),
        "null_max_media": round(float(null_max.mean()), 4),
        "null_max_p95": round(float(np.percentile(null_max, 95)), 4),
        "p_valor_permutacion": round(p, 4),
        "veredicto": "RUIDO (no distinguible del azar)" if p > 0.05 else "SENAL (supera el azar)",
    }

def main():
    df = pd.read_csv(CLEAN, encoding="utf-8")
    val = df[df["anomalia"] == 0]
    out = {"n_permutaciones": N_PERM, "semilla": SEED, "generador": "uno por test, cada uno con semilla 42",
           "base": "ventas validas (sin las 16 anomalias)"}

    # ---------- P1 ----------
    rng = np.random.default_rng(SEED)
    ultimo = df["anio_mes"].max()
    tot = val.groupby("anio_mes")["importe"].sum()
    tot = tot[tot.index != ultimo]
    meses = np.array([int(k[5:]) for k in tot.index])
    valores = tot.values
    def max_media(etq):
        return pd.Series(valores).groupby(etq).mean().max()
    medias = pd.Series(valores).groupby(meses).mean()
    obs = float(medias.max())
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        null[i] = max_media(rng.permutation(meses))
    p1 = float((null >= obs).mean())
    out["p1_estacionalidad"] = {
        "estadistico": "maxima media de facturacion mensual por mes del anio (meses completos, sin anomalias)",
        "n_meses": int(len(tot)),
        "mes_observado": int(medias.idxmax()),
        "media_observada": round(obs, 2),
        "null_max_media": round(float(null.mean()), 2),
        "null_max_p95": round(float(np.percentile(null, 95)), 2),
        "p_valor_permutacion": round(p1, 4),
        "veredicto": "RUIDO (ningun mes destaca mas que el azar)" if p1 > 0.05 else "SENAL (estacionalidad real)",
        "lectura": "p = fraccion de barajados en que el mejor mes del azar iguala o supera al mejor mes real",
    }

    # ---------- P2 ----------
    sat = val.dropna(subset=["satisfaccion"])
    out["p2_region_satisfaccion"] = test_p2(sat, "validas con satisfaccion, 2019-2026")
    out["p2_region_satisfaccion_sin_2026"] = test_p2(sat[sat["anio"] < 2026], "validas con satisfaccion, 2019-2025")

    out["p3_correlacion"] = {"nota": "se contrasta en 05_eda.py con pearsonr y spearmanr de scipy (p exacto)"}

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("== ROBUSTEZ ==")
    print("P1:", out["p1_estacionalidad"])
    print("P2:", out["p2_region_satisfaccion"])
    print("P2 sin 2026:", out["p2_region_satisfaccion_sin_2026"])

if __name__ == "__main__":
    main()
