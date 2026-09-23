# Informe técnico del histórico de ventas de TechSoluciones S.L. entre 2019 y 2026

> Caso ficticio con datos sintéticos. Todas las cifras salen de los ficheros de `analisis/salidas/`, que
> producen los scripts `analisis/01` a `10`. Versión corregida el 13/09/2026 y puesta al día el
> 23/09/2026.

## Resumen para dirección

**El fichero tiene 16 ventas fuera de las reglas del catálogo y ningún patrón que explotar.** Las 16
llevan entre 41 y 45 unidades cuando el resto va de 1 a 5, y 12 de ellas un precio doble o triple del de
catálogo. Suman 798.360 €, el 1,63 % de lo registrado. Todo apunta a errores de registro, sin confirmar.
Se han marcado y apartado del análisis sin corregirlas.

Sobre las 19.984 ventas válidas:

| Pregunta del encargo | Respuesta | Confianza |
|---|---|---|
| ¿Mes con mayores ventas? | octubre de 2023, 709.580 € | alta: es un cálculo directo |
| ¿Hay un mes del año que venda más? | agosto tiene la media más alta (+4,49 %), pero el azar la iguala en el 87 % de los casos | no hay evidencia de estacionalidad |
| ¿Región con mayor crecimiento en satisfacción? | Navarra por pendiente, pero no supera al azar (p = 0,60); sin 2026 sale Madrid (p = 0,36) | ninguna región destaca |
| ¿Correlación ventas y satisfacción? | r = 0,0034 sobre 15.980 ventas | ninguna relación útil |

La facturación de 2019 a 2025 cae un 1,31 % y la satisfacción media es 5,5 sobre 10. Con este dato no se
pueden segmentar clientes. 5.035 correos los usan personas con nombre distinto. Los 97 nombres que aparecen dos
veces llevan teléfonos distintos, así que son homónimos: nadie compra dos veces.

## 1 · Contexto

La dirección entrega 20.827 filas de ventas de 2019 a mayo de 2026, con 11 columnas y problemas de
calidad. El encargo tiene cuatro tareas: preparar y documentar el dato (A), anonimizarlo (B), explorarlo
y detectar anomalías (C) y construir un cuadro de mando que responda tres preguntas de negocio (D). El
cuadro de mando se ha construido en la web del proyecto (`web/`) en lugar de Power BI. La web tiene 63
páginas: las del encargo y 39 más que explican, con estos mismos datos, 60 conceptos de estadística
descriptiva, atípicos, inferencia, aprendizaje automático y cuadros de mando.

## 2 · Tarea A · preparación del dato

`02_etl.py` parte siempre del fichero crudo y registra cada paso en `etl_log.json`.

| Paso | Qué hace | Conteo |
|---|---|---|
| Duplicados | elimina filas idénticas en todas las columnas | 827 eliminadas: 20.827 → 20.000 |
| Productos | unifica variantes con y sin tilde | 10 → 8 |
| Provincias | unifica nombres oficiales, tradicionales y abreviados | 55 → 52 |
| Email | quita espacios, pasa a minúsculas y quita tildes | 9.024 corregidos: 884 con espacio y 8.952 con tilde, 812 con los dos; quedan 12.957 distintos |
| Fechas | reconoce cuatro formatos y pasa a ISO; deriva año, mes y trimestre | 0 sin reconocer |
| Importe | `cant × precio` | · |
| Satisfacción | numérica 1-10; los vacíos se dejan nulos | 4.006 nulos (20,03 %) |
| Anomalías | marca cantidad fuera de 1-5 o precio distinto del de catálogo | 16 ventas |

La ausencia de satisfacción es compatible con aleatoria: la prueba chi-cuadrado no encuentra diferencia
por provincia (p = 0,68), año (p = 0,998), producto (p = 0,57) ni categoría (p = 0,44). Por eso se
analizan los casos disponibles sin imputar. La prueba no puede ver si la ausencia depende de la propia
nota que falta.

**Datos personales.** El diccionario (`diccionario.json`, 18 campos con tipo, descripción, regla de
limpieza y valores) marca como identificadores directos el nombre, el email y el teléfono, y como
cuasi-identificadores la fecha y la provincia.

## 3 · Tarea B · anonimización

Salen dos ficheros, porque no tienen el mismo uso.

**Interno** (`data/techsoluciones_ventas_anon.csv`). Sin nombre, con email y teléfono enmascarados y un
`cliente_id` para cada una de las 20.000 personas. La clave es nombre más teléfono: el email lo comparten
personas distintas y el nombre tiene homónimos. Los números se barajan con un generador de semilla 42
para que el orden no delate a nadie. Conserva fecha, producto e importe, así que no se publica.

**Público** (`data/techsoluciones_ventas_publico.csv`). Solo año, provincia, satisfacción y la marca de
anomalía. Las cifras de venta se publican agregadas en el cuadro de mando.

| Columnas que identifican | k mínima | Ventas únicas | Ventas en grupos de menos de 5 |
|---|---|---|---|
| año + provincia (lo publicado) | 10 | 0 | 0 % |
| + categoría (no se publica) | 4 | 0 | 0,06 % |
| + categoría + producto (no se publica) | 1 | 169 | 17,75 % |
| + categoría + producto + cantidad (no se publica) | 1 | 5.522 | · |

El fichero público cumple k = 10 y l = 5 sobre la satisfacción sin suprimir ninguna venta. La l no cuenta
el valor vacío como un valor más; contándolo sería 6. El producto no se publica. Tampoco el precio, la
cantidad ni el importe por venta: cada producto tiene un precio de catálogo único, así que cualquiera de
esas columnas lo revela. Quien supiera qué compró alguien, cuándo y
dónde, encontraría 169 ventas solas en su grupo y leería su satisfacción.

Una primera versión de este mismo día publicaba el producto y agrupaba por nombre. Lo encontró la revisión
escéptica del paso de verificación, y está corregido.

## 4 · Tarea C · exploración y anomalías

### Descriptivos de las ventas válidas

| Variable | Media | Mediana | Desviación | Mín | Máx |
|---|---|---|---|---|---|
| Importe (€) | 2.405,41 | 1.200 | 3.336,10 | 45 | 17.500 |
| Unidades | 2,99 | 3 | 1,40 | 1 | 5 |
| Precio (€) | 806,23 | 300 | 956,53 | 45 | 3.500 |
| Satisfacción | 5,50 | 5 | 2,88 | 1 | 10 |

Tres productos de precio alto (servidor, portátil y ERP) reúnen el 80 % de la facturación. Entre
provincias está mucho más repartida: hacen falta 40 de las 52 para llegar al 80 %.

### Las 16 anomalías

Todas tienen un identificador múltiplo de 50 y una cantidad de 41 a 45, que es 40 más una cantidad normal.
No hay ninguna venta de 6 a 40 unidades. Doce tienen
además un precio exactamente doble o triple del de catálogo, un precio que no aparece en ninguna venta
normal. La lista completa, con fecha, producto, precio y precio de catálogo, está en `eda.json`
(`anomalias.lista`) y en la página 8 de la web.

Causas propuestas, **todas hipótesis sin confirmar**:

1. un 4 tecleado de más delante de la cantidad al registrar la venta;
2. un precio de otra tarifa, o de un lote, multiplicado por 2 o por 3;
3. errores introducidos a propósito al generar el dataset, por lo regular de sus identificadores.

No se corrigen, porque el valor verdadero no se conoce. Quien registró las ventas tiene que validarlas.

No hay ventas extremadamente bajas: la más baja es de 45 €, una unidad del producto más barato.

### Lo que parece atípico y no es un error

El rango intercuartílico sobre el importe marca 1.588 ventas: las 16 anomalías y 1.572 ventas normales
del servidor, que es el producto más caro. Mezclar productos de 45 € y de 3.500 € confunde caro con
extraño. Dentro de cada producto la cantidad va de 1 a 5, y el mismo método aplicado por producto aísla
exactamente las 16.

### Detección automática

IsolationForest, sin conocer la regla, marca 760 ventas sobre las 20.000. Caza 15 de las 16 anomalías y
se le escapa V0050 (44 switches por 7.920 €, un importe bajo). Las otras 745 que marca son ventas normales
del servidor. Sirve para proponer candidatas; la regla de negocio decide.

## 5 · Tarea D · cuadro de mando y preguntas de negocio

La página 17 de la web reúne lo que pide el encargo: KPI de facturación válida y registrada, crecimiento
2019-2025 (−1,31 %) con su detalle interanual, satisfacción media (5,5), tendencia mensual, mapa de calor
por provincia y año, facturación por producto y provincia, y una tabla de alertas con las 16 anomalías.

### P1 · mes con mayores ventas

Octubre de 2023, con 709.580 €. El segundo fue enero de 2019, con 689.080 €. Es el máximo en euros; en
número de ventas gana junio de 2022 (264) y en unidades enero de 2019 (791). Tampoco es un pico: está 2,93
desviaciones sobre la media de los meses completos, por debajo del umbral de Grubbs para 88 meses.

Para saber si algún mes del año vende más hay que evitar dos sesgos. Enero a abril tienen ocho años
completos y el resto siete, porque mayo de 2026 está a medias. Sumando ganaría marzo, por tener un año más.
Y las anomalías inflan el mes en que caen. Comparando la media mensual sobre los 88 meses completos y sin
anomalías, agosto queda el primero con 565.549 €, un 4,49 % sobre la media. Un test de permutación que
baraja las etiquetas de mes 2.000 veces y mide lo mismo, la media más alta de un mes del año, da p = 0,866.
No hay evidencia de estacionalidad. Con 7 u 8 años por mes el test solo detectaría diferencias grandes, así
que una estacionalidad suave no queda descartada.

### P2 · región con mayor crecimiento en satisfacción

Medido como la pendiente de la satisfacción media anual, Navarra es la primera (pasa de 4,58 a 6,56). Con
52 provincias alguna tenía que serlo: barajando la satisfacción 2.000 veces, el azar produce una pendiente
igual o mayor con p = 0,60. Sin 2026, que solo tiene unos meses, la primera pasa a ser Madrid y el test da
p = 0,36. Ninguna región crece más de lo que se puede distinguir del azar, y la que sale primera cambia según el periodo
y la forma de medir.

### P3 · correlación entre ventas y satisfacción

Pearson r = 0,0034 (p = 0,67) y Spearman r = −0,0002 sobre 15.980 ventas válidas con satisfacción. Entre
unidades y satisfacción sale r = 0,0194 con p = 0,014: distinto de cero por el tamaño de la muestra, pero
explica el 0,04 % de la variación. No hay relación útil para el negocio. Un modelo de regresión y un
bosque aleatorio tampoco predicen la satisfacción (R² de test −0,002 en los dos).

## 6 · Verificación

Tres comprobaciones, cada una con un método distinto del que produjo las cifras.

**Banco de comprobaciones** (`analisis/verificar_correcciones.py`). Dieciocho casos: uno por defecto
corregido el 13/09, la matriz de los 19 requisitos del encargo con su evidencia en disco y, desde el
23/09, tres más sobre las lecturas de los resultados. Sale todo en verde sobre este proyecto. El 13/09,
sobre la copia de antes de corregir, salía en rojo 14 de 15; el que quedaba en verde, el mes con mayores
ventas, ya estaba bien y está puesto como control de que no se estropea.

**Recálculo independiente.** Un verificador rehízo desde el CSV crudo, con su propio código y solo la
biblioteca estándar de Python, 16 cifras: filas únicas, facturación registrada y válida, anomalías y su
importe, ticket, satisfacción, crecimiento, los dos meses de la P1, la correlación, k y l, clientes y
emails. Cuadran las 16. Anotó dos criterios que conviene saber: la l = 5 no cuenta el vacío, y los
emails distintos son 12.957 sobre las 20.000 ventas y 12.953 sobre las válidas.

**Revisión escéptica.** Otro agente intentó tumbar las siete conclusiones con métodos distintos
(Kruskal-Wallis y ANOVA para los meses, regresión por venta para las provincias, Grubbs para octubre de
2023). No refutó ninguna y matizó cinco. Encontró además dos defectos, ya corregidos: el fichero público
llevaba el producto y el pseudónimo juntaba homónimos.

**Revisión completa del 23/09.** Se releyeron las 63 páginas y cada cifra dudosa se recalculó desde el
bruto o reproduciendo el cálculo. Salieron errores de lectura de cifras correctas: el más serio atribuía
a la mezcla de productos el 98,2 % de una diferencia que la mezcla explica entera. En la limpieza, los
correos corregidos contaban dos veces 812 que tenían los dos defectos. Y once textos de lectura de los
resultados decían algo que el dato no sostiene. Todo quedó corregido y el banco vigila que no vuelva.

## 7 · Limitaciones

- Las causas de las anomalías son hipótesis; solo el origen del dato puede confirmarlas.
- 2026 está incompleto y se excluye de los crecimientos y de la comparación de meses.
- Un 20 % de la satisfacción falta. La ausencia es compatible con el azar por provincia, año, producto y
  categoría. Queda sin cruzar con el importe y la cantidad, y no se puede descartar que dependa de la propia nota.
- La clave de persona es nombre más teléfono. Si una misma persona cambió de teléfono contaría como dos.
- El encargo sugería Power BI, sus funciones de anomalías y de preguntas en lenguaje natural, y ARX para la
  anonimización. No se han usado: el cuadro de mando está en la web, las anomalías y las preguntas se
  resuelven con Python, y k y l se calculan con pandas.
- No se ha contrastado el crecimiento de ventas por provincia; solo el de satisfacción, que es lo que pregunta la P2.
- Los datos son sintéticos: la falta de patrones puede venir de cómo se generaron.

## 8 · Cómo reproducirlo

```bash
cd analisis
python 01_perfilado.py && python 02_etl.py && python 03_diccionario.py && python 04_anonimizacion.py
python 05_eda.py && python 06_robustez.py && python 07_ml.py
python 08_inferencia.py && python 09_segmentacion.py && python 10_atipicos_kpi.py
cp salidas/*.json ../web/src/data/
python verificar_correcciones.py        # banco de comprobaciones, todo en VERDE
cd ../web && npm run build
```

El primer script lee el fichero original, que no se publica porque contiene datos personales. Quien solo
tenga el repositorio ve los resultados en la web y el fichero anonimizado, pero no puede ejecutar la cadena.

Requiere Python con pandas, numpy, scipy y scikit-learn, y Node para la web. Las semillas son fijas, así que
dos ejecuciones dan los mismos ficheros.
