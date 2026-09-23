# -*- coding: utf-8 -*-
"""
01_perfilado.py: Inspeccion/perfilado del dataset crudo (paso 2 del guion).
Solo LECTURA. No modifica el CSV. Vuelca un JSON con el diagnostico + imprime resumen.
Objetivo: entender la suciedad ANTES de decidir la limpieza y el diccionario.
"""
import csv, json, re, collections, os, sys

RAW = os.path.join(os.path.dirname(__file__), "..", "..", "techsoluciones_ventas_dirty.csv")
OUT = os.path.join(os.path.dirname(__file__), "salidas", "perfilado.json")

def sniff_encoding(path):
    with open(path, "rb") as f:
        head = f.read()
    # UTF-8 valido?
    try:
        head.decode("utf-8")
        utf8_ok = True
    except UnicodeDecodeError:
        utf8_ok = False
    # patron de mojibake tipico (UTF-8 leido como latin1): 'Ã' seguido de algo
    txt_latin1 = head.decode("latin-1", errors="replace")
    mojibake_hits = len(re.findall(r"Ã.|Â.", txt_latin1))
    return {"utf8_valido": utf8_ok, "bytes": len(head), "mojibake_latin1_hits": mojibake_hits}

def is_number(s):
    try:
        float(s); return True
    except: return False

def main():
    enc = sniff_encoding(RAW)
    with open(RAW, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        rows = list(reader)
    n = len(rows)

    prof = {"n_filas": n, "columnas": cols, "encoding": enc, "campos": {}}

    for c in cols:
        vals = [r[c] for r in rows]
        nonempty = [v for v in vals if v is not None and v.strip() != ""]
        empties = n - len(nonempty)
        uniq = collections.Counter(nonempty)
        info = {
            "n_vacios": empties,
            "pct_vacios": round(100*empties/n, 2),
            "n_distintos": len(uniq),
        }
        # De los identificadores directos no se guardan valores: el JSON va al repositorio publico (23/09/2026)
        if c not in ("nombre_completo", "email", "telefono"):
            info["top5"] = uniq.most_common(5)
        # numerico?
        num = [float(v) for v in nonempty if is_number(v)]
        if c in ("nombre_completo", "email", "telefono"):
            num = []  # un telefono no es una magnitud, y su minimo y su maximo son telefonos
        if num and len(num) >= 0.5*len(nonempty):
            info["numerico"] = {
                "n_numericos": len(num),
                "min": min(num), "max": max(num),
                "media": round(sum(num)/len(num), 3),
            }
            # valores no numericos dentro de un campo aparentemente numerico
            no_num = [v for v in nonempty if not is_number(v)]
            info["no_numericos_muestra"] = no_num[:10]
        prof["campos"][c] = info

    # --- Diagnosticos especificos de suciedad ---
    diag = {}

    # fechas: detectar formatos
    fechas = [r["fecha_str"] for r in rows if r["fecha_str"].strip()]
    patrones = collections.Counter()
    def clasifica_fecha(s):
        s = s.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", s): return "ISO aaaa-mm-dd"
        if re.match(r"^\d{2}/\d{2}/\d{2}$", s): return "xx/xx/aa (barra, 2 dig anio)"
        if re.match(r"^\d{2}/\d{2}/\d{4}$", s): return "xx/xx/aaaa (barra)"
        if re.match(r"^\d{2}-\d{2}-\d{4}$", s): return "dd-mm-aaaa (guion)"
        if re.match(r"^\d{4}/\d{2}/\d{2}$", s): return "aaaa/mm/dd"
        return "OTRO: " + s
    for s in fechas: patrones[clasifica_fecha(s)] += 1
    diag["formatos_fecha"] = patrones.most_common(20)

    # satisfaccion: distribucion + fuera de escala 1-5
    sat = [r["satisfaccion"].strip() for r in rows]
    sat_dist = collections.Counter(sat)
    diag["satisfaccion_dist"] = sat_dist.most_common(20)

    # productos: posibles duplicados por normalizacion (minus/sin acento)
    def norm(s):
        s = s.lower().strip()
        for a,b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u")]:
            s = s.replace(a,b)
        return s
    prod_groups = collections.defaultdict(set)
    for r in rows:
        prod_groups[norm(r["prod"])].add(r["prod"])
    dup_prod = {k: sorted(v) for k,v in prod_groups.items() if len(v) > 1}
    diag["productos_variantes"] = dup_prod

    # emails con espacios / sin @ / raros
    mails = [r["email"] for r in rows]
    diag["email_con_espacio"] = sum(1 for m in mails if " " in m)
    diag["email_sin_arroba"] = sum(1 for m in mails if "@" not in m)

    # telefonos: longitudes
    tel_len = collections.Counter(len(re.sub(r"\D","", r["telefono"])) for r in rows)
    diag["telefono_longitudes"] = tel_len.most_common(20)

    # duplicados
    ids = collections.Counter(r["id_venta"] for r in rows)
    diag["id_venta_duplicados"] = sum(1 for k,v in ids.items() if v>1)
    full = collections.Counter(tuple(r[c] for c in cols) for r in rows)
    diag["filas_identicas_duplicadas"] = sum(v-1 for v in full.values() if v>1)

    # cant y precio negativos/cero
    def to_f(x):
        try: return float(x)
        except: return None
    diag["cant_no_positiva"] = sum(1 for r in rows if (to_f(r["cant"]) is not None and to_f(r["cant"])<=0))
    diag["precio_no_positivo"] = sum(1 for r in rows if (to_f(r["precio"]) is not None and to_f(r["precio"])<=0))

    prof["diagnostico_suciedad"] = diag

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(prof, f, ensure_ascii=False, indent=2)

    # --- resumen a consola ---
    print("== PERFILADO ==")
    print("Filas:", n, "| Columnas:", len(cols))
    print("Encoding:", enc)
    print("\n-- Vacios por campo --")
    for c in cols:
        print(f"  {c:16} vacios={prof['campos'][c]['n_vacios']:5} ({prof['campos'][c]['pct_vacios']}%)  distintos={prof['campos'][c]['n_distintos']}")
    print("\n-- Formatos de fecha --")
    for k,v in diag["formatos_fecha"]: print(f"  {v:6}  {k}")
    print("\n-- Satisfaccion --")
    for k,v in diag["satisfaccion_dist"]: print(f"  '{k}': {v}")
    print("\n-- Productos con variantes (mismo producto, distinta escritura) --")
    for k,v in list(dup_prod.items())[:30]: print(f"  {v}")
    print("\n-- Suciedad varia --")
    for k in ["email_con_espacio","email_sin_arroba","telefono_longitudes","id_venta_duplicados","filas_identicas_duplicadas","cant_no_positiva","precio_no_positivo"]:
        print(f"  {k}: {diag[k]}")
    print("\nJSON ->", OUT)

if __name__ == "__main__":
    main()
