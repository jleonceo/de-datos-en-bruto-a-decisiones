# -*- coding: utf-8 -*-
"""
03_diccionario.py: Diccionario de datos (Tarea A). Combina descripcion autoral
con estadisticos calculados del CSV limpio. Vuelca salidas/diccionario.json.
"""
import pandas as pd, json, os

HERE = os.path.dirname(__file__)
CLEAN = os.path.join(HERE, "..", "data", "techsoluciones_ventas_clean.csv")
OUT = os.path.join(HERE, "salidas", "diccionario.json")

# Descripcion autoral por campo (el "que es" y las reglas; los numeros se calculan abajo)
CAMPOS = [
    ("id_venta", "Texto", "Identificador único de la venta.", "No (ID de transaccion)",
     "Formato Vxxxx. Se uso para detectar 827 filas duplicadas exactas."),
    ("fecha", "Fecha (ISO)", "Fecha de la venta, estandarizada a AAAA-MM-DD.", "Cuasi-identificador",
     "Derivada de 'fecha_str', que venia en 4 formatos distintos; parseo por formato."),
    ("anio", "Entero", "Año de la venta (derivado de la fecha).", "No", "Derivado."),
    ("mes", "Entero", "Mes de la venta, de 1 a 12 (derivado de la fecha).", "No", "Derivado."),
    ("anio_mes", "Texto", "Periodo AAAA-MM, para las series temporales.", "No", "Derivado."),
    ("trimestre", "Texto", "Trimestre natural AAAA-Tn.", "No", "Derivado."),
    ("nombre_completo", "Texto", "Nombre y apellidos del cliente.", "SI, identificador directo",
     "Colapso de espacios multiples. Anonimizado -> cliente_id en el dataset entregable."),
    ("email", "Texto", "Correo electrónico del cliente.", "SI, identificador directo",
     "884 emails con espacios internos y 8.952 con tildes, corregidos; pasado a minusculas. "
     "Quedan 12.957 emails distintos. Varias personas comparten email: no sirve como clave de cliente. "
     "Enmascarado en el fichero interno y retirado del publico."),
    ("telefono", "Texto", "Teléfono del cliente (9 dígitos).", "SI, identificador directo",
     "Dejados solo digitos. Enmascarado en el entregable."),
    ("reg", "Categórico", "Provincia española del cliente.", "Cuasi-identificador",
     "Colapsadas variantes (Gerona/Girona, Lerida/Lleida, Sta. Cruz/Santa Cruz de Tenerife): 55 -> 52."),
    ("cat", "Categórico", "Categoría del producto: Software o Hardware.", "No", "Sin incidencias; cada producto tiene una sola categoria."),
    ("prod", "Categórico", "Producto vendido (8 productos).", "No",
     "Canonicalizadas variantes por acentos (Modulo/Modulo Nominas, Portatil/Portatil): 10 -> 8."),
    ("cant", "Entero", "Unidades vendidas en la venta.", "No",
     "Rango dominante 1-5. 16 ventas con 41-45 unidades, marcadas como anomalia (no se corrigen)."),
    ("precio", "Decimal (EUR)", "Precio unitario del producto.", "No",
     "8 precios de catalogo, uno por producto. 12 ventas con precio x2 o x3 del de catalogo, marcadas como anomalia."),
    ("importe", "Decimal (EUR)", "Importe total de la venta: cant × precio.", "No", "Calculado en el ETL."),
    ("satisfaccion", "Entero 1-10 (admite vacíos)", "Satisfacción declarada por el cliente, de 1 a 10.", "No",
     "20% de valores ausentes; NO se imputan (se analizan los casos disponibles). Ausencia aleatoria: "
     "chi-cuadrado por provincia, anio, producto y categoria sin diferencia significativa (ver eda.json)."),
    ("anomalia", "Entero 0/1", "1 si la venta rompe las reglas del catálogo (cantidad o precio).", "No",
     "Regla: cantidad fuera de 1-5 o precio distinto del de catalogo de su producto. Excluidas de los KPI."),
    ("motivo_anomalia", "Texto (admite vacíos)", "Por qué la venta se marcó como anomalía.", "No",
     "Vacio en las ventas validas. Nombra la cantidad y, si aplica, el multiplo del precio de catalogo."),
]

FORMATO_IDENTIFICADOR = {
    "nombre_completo": "nombre y apellidos en texto libre",
    "email": "usuario@dominio, en minusculas y sin tildes tras la limpieza",
    "telefono": "9 digitos",
}

def main():
    df = pd.read_csv(CLEAN, encoding="utf-8")
    items = []
    for nombre, tipo, desc, pii, regla in CAMPOS:
        s = df[nombre]
        nn = s.dropna()
        info = {
            "campo": nombre, "tipo": tipo, "descripcion": desc, "pii": pii, "regla_limpieza": regla,
            "n_nulos": int(s.isna().sum()) + int((s.astype(str) == "").sum()),
            "n_distintos": int(nn.nunique()),
        }
        # valores posibles / rango
        if info["n_distintos"] <= 15 and tipo.startswith(("Categ", "Entero")) and nombre != "id_venta":
            info["valores_posibles"] = sorted([str(x) for x in nn.unique()])[:20]
        else:
            # De los identificadores directos no se guarda ningun valor, ni ejemplos ni rango: el JSON
            # se publica (23/09/2026). Se describe su formato en su lugar.
            if pii.startswith("SI"):
                info["formato"] = FORMATO_IDENTIFICADOR[nombre]
            else:
                if pd.api.types.is_numeric_dtype(nn):
                    info["rango"] = [float(nn.min()), float(nn.max())]
                info["ejemplos"] = [str(x) for x in nn.head(3).tolist()]
        items.append(info)

    out = {"n_campos": len(items), "n_filas": int(len(df)), "campos": items}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Diccionario:", len(items), "campos ->", OUT)
    for it in items:
        print(f"  {it['campo']:16} {it['tipo']:20} PII={it['pii'][:3]:3} nulos={it['n_nulos']:5} dist={it['n_distintos']}")

if __name__ == "__main__":
    main()
