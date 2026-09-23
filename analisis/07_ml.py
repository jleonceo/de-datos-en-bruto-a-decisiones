# -*- coding: utf-8 -*-
"""
07_ml.py: Machine Learning, con lo que el dato permite y lo que no:
  A) ¿Se pueden segmentar clientes? Se mide si existe una clave de cliente y si hay recompra.
     Sin clave fiable ni recompra, un RFM + KMeans daria segmentos falsos, asi que no se entrena.
  B) Predecir la satisfaccion sobre ventas validas -> R^2 ~ 0 (el ML no inventa senal).
  C) IsolationForest sobre las 20.000 ventas y cuantas de las 16 anomalias de la regla caza.
Determinista (random_state=42). Vuelca analisis/salidas/ml.json.
"""
import pandas as pd, numpy as np, json, os
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.dummy import DummyRegressor

HERE = os.path.dirname(__file__)
CLEAN = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT = os.path.join(HERE, "salidas", "ml.json")
SEED = 42

def r3(x):
    try: return round(float(x), 3)
    except (TypeError, ValueError): return None

def main():
    df = pd.read_csv(CLEAN, encoding="utf-8")
    val = df[df["anomalia"] == 0].copy()
    out = {"seed": SEED}

    # ============ A) SEGMENTACION DE CLIENTES: ¿es viable? ============
    nombres_por_email = val.groupby("email")["nombre_completo"].nunique()
    emails_por_nombre = val.groupby("nombre_completo")["email"].nunique()
    compras = val.groupby("nombre_completo").size()
    repetidos = val[val["nombre_completo"].map(compras) > 1]
    tel_por_repetido = repetidos.groupby("nombre_completo")["telefono"].nunique()
    compras_persona = val.groupby(["nombre_completo", "telefono"]).size()
    out["segmentacion_clientes"] = {
        "viable": False,
        "base": "ventas validas",
        "clientes_por_email": int(val["email"].nunique()),
        "clientes_por_nombre": int(val["nombre_completo"].nunique()),
        "emails_con_varios_nombres": int((nombres_por_email > 1).sum()),
        "max_nombres_por_email": int(nombres_por_email.max()),
        "nombres_con_varios_emails": int((emails_por_nombre > 1).sum()),
        "pct_una_compra_por_nombre": round(100 * float((compras == 1).mean()), 2),
        "max_compras": int(compras.max()),
        "nombres_con_dos_o_mas_compras": int(len(tel_por_repetido)),
        "de_ellos_con_telefonos_distintos": int((tel_por_repetido > 1).sum()),
        "personas_por_nombre_y_telefono": int(len(compras_persona)),
        "pct_una_compra_por_persona": round(100 * float((compras_persona == 1).mean()), 2),
        "motivo": "el email lo comparten personas distintas, asi que agrupar por email mezcla clientes; "
                  "los pocos nombres que repiten tienen telefonos distintos, o sea son homonimos; "
                  "por persona nadie compra dos veces, asi que no hay Frecuencia ni Recencia que "
                  "separe grupos. Un KMeans sobre esto produce segmentos que describen el algoritmo, no a los clientes.",
        "que_haria_falta": "un identificador de cliente en origen y varios anios de recompra",
    }

    # ============ B) MODELO HONESTO: predecir satisfaccion (validas) ============
    d = val.dropna(subset=["satisfaccion"]).copy()
    num = ["importe", "cant", "precio", "mes"]
    cat = ["cat", "prod", "reg"]
    pre = ColumnTransformer([("num", StandardScaler(), num),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), cat)])
    Xy = d[num + cat]
    y = d["satisfaccion"].values
    Xtr, Xte, ytr, yte = train_test_split(Xy, y, test_size=0.2, random_state=SEED)
    modelos = {
        "baseline_media": DummyRegressor(strategy="mean"),
        "regresion_lineal": Pipeline([("pre", pre), ("m", LinearRegression())]),
        "random_forest": Pipeline([("pre", pre), ("m", RandomForestRegressor(
            n_estimators=200, max_depth=12, random_state=SEED, n_jobs=-1))]),
    }
    res = {}
    for nombre, mod in modelos.items():
        if nombre == "baseline_media":
            mod.fit(Xtr[num], ytr); pred = mod.predict(Xte[num])
        else:
            mod.fit(Xtr, ytr); pred = mod.predict(Xte)
        res[nombre] = {"r2_test": r3(r2_score(yte, pred)), "mae_test": r3(mean_absolute_error(yte, pred))}
    out["prediccion_satisfaccion"] = {
        "base": "ventas validas con satisfaccion",
        "n_train": int(len(Xtr)), "n_test": int(len(Xte)), "resultados": res,
        "conclusion": "R^2 de test ~ 0: con estas variables la satisfaccion no se puede predecir.",
    }

    # ============ C) ANOMALIAS: IsolationForest contra la regla del ETL ============
    feats = df[["importe", "cant", "precio"]].astype(float)
    iso = IsolationForest(contamination=0.05, random_state=SEED, n_estimators=200)
    df["_iso"] = iso.fit_predict(feats)  # -1 = anomalia
    marcadas = df["_iso"] == -1
    regla = df["anomalia"] == 1
    no_cazadas = df[regla & ~marcadas]
    out["anomalias"] = {
        "base": "las 20.000 ventas registradas",
        "isolationforest_n": int(marcadas.sum()),
        "anomalias_regla_n": int(regla.sum()),
        "anomalias_regla_cazadas": int((marcadas & regla).sum()),
        "anomalias_regla_no_cazadas": no_cazadas[["id_venta", "prod", "cant", "precio", "importe"]].to_dict("records"),
        "marcadas_que_no_son_anomalia_de_regla": int((marcadas & ~regla).sum()),
        "marcadas_normales_por_producto": {k: int(v) for k, v in df[marcadas & ~regla]["prod"].value_counts().items()},
        "lectura": "IsolationForest no conoce la regla: aisla lo raro en importe, cantidad y precio a la vez. "
                   "Caza casi todas las ventas de la regla, pero marca tambien cientos de ventas normales de "
                   "productos caros. Sirve de contraste para encontrar candidatas; la regla de negocio decide.",
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("== ML ==")
    print("A)", {k: v for k, v in out["segmentacion_clientes"].items() if k not in ("motivo", "que_haria_falta")})
    print("B) R2 test:", {k: v["r2_test"] for k, v in res.items()})
    a = out["anomalias"]
    print("C) ISO marca", a["isolationforest_n"], "| caza", a["anomalias_regla_cazadas"], "de", a["anomalias_regla_n"],
          "| no cazadas:", a["anomalias_regla_no_cazadas"], "| normales marcadas:", a["marcadas_normales_por_producto"])

if __name__ == "__main__":
    main()
