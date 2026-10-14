English version: [README.en.md](README.en.md)

# Ventas: de un fichero en bruto a un cuadro de mando

Análisis completo de un fichero de ventas en bruto para contestar tres preguntas de negocio: qué mes vende más,
qué provincia mejora más en satisfacción y si la satisfacción acompaña a las ventas. Recorre limpieza,
anonimización, análisis exploratorio, contraste estadístico y diseño del cuadro de mando, y lo cuenta en una web
de 63 páginas.

**Resultado:** ninguna de las tres preguntas tiene la respuesta que daba por hecha. El mejor mes, la provincia
que más mejora y la relación entre satisfacción e importe no se distinguen del azar con estos datos. Cada cifra
de la web se recalculó desde el fichero original antes de publicarla.

Web: [de-datos-en-bruto-a-decisiones.vercel.app](https://de-datos-en-bruto-a-decisiones.vercel.app)

```bash
cd web
npm install
npm run dev
```

Hace falta Node 22.12 o posterior. `npm run build` genera la web estática en `web/dist`.

## El problema de partida

Una pyme ficticia, TechSoluciones S.L., tiene sus ventas de 2019 a mayo de 2026 en un fichero. Trae fechas en
cuatro formatos, productos escritos de dos maneras, 827 filas duplicadas y 16 ventas imposibles. Con ese fichero
se monta un cuadro de mando en una tarde, pero casi todo lo que enseñaría sería ruido.

## Lo que sale

| Pregunta | Qué dicen los datos |
|---|---|
| ¿Qué mes vende más? | Octubre de 2023, con 709.580 €. Agosto tiene la media más alta, un 4,49 % por encima, pero barajando los datos el azar da un ganador así en el 87 % de los casos |
| ¿Qué provincia mejora más en satisfacción? | Navarra, aunque el azar da una mejora igual o mayor en 60 de cada 100 barajados. Sin 2026, que está incompleto, pasa a ser Madrid |
| ¿La satisfacción acompaña a las ventas? | No. La correlación entre importe y satisfacción es de 0,0034 sobre 15.980 ventas |

Tampoco se pueden segmentar los clientes: el fichero no trae un código de cliente, 5.035 correos los usan
personas con nombres distintos y, contando por nombre y teléfono, nadie compra dos veces.

## Qué hay dentro

1. `analisis/` contiene los diez scripts de Python, en el orden en que se ejecutan: perfilado, limpieza,
   diccionario, anonimización, análisis exploratorio, robustez, modelos, inferencia, segmentación y atípicos.
2. `analisis/salidas/` guarda sus resultados en JSON, que son los que lee la web.
3. `analisis/verificar_correcciones.py` repite 19 comprobaciones de errores que ya se cometieron una vez, entre
   ellas que ningún fichero publicado lleve un nombre, un correo o un teléfono.
4. `web/` es la web, hecha con Astro, Tailwind y daisyUI. Cada concepto tiene su página: el problema, por qué
   engaña, la solución y lo que pasa con estos datos.
5. `data/` contiene el fichero anonimizado que se puede publicar.
6. `INFORME_TECNICO.md` recoge el informe técnico completo, con las decisiones de cada paso.

## Cómo se comprobó

Ningún modelo de lenguaje calcula las cifras de la web: salen de los scripts, con semilla fija. Antes de
publicar, tres verificadores recalcularon desde el fichero original, con código propio, 1.439 cifras de las
páginas. Las que no cuadraban por redondeo o por cómo las leía la página se corrigieron. Un revisor intentó
refutar 51 conclusiones. Cinco no se sostenían y se corrigieron.

## Límites

- El fichero original no se publica porque contiene nombres, correos y teléfonos, aunque sean inventados. Con
  el fichero anonimizado, que solo lleva año, provincia, satisfacción y la marca de anomalía, no se puede
  ejecutar la cadena de scripts.
- Por el mismo motivo, cuatro de las 19 comprobaciones (C1, C2, C7 y C16) salen en rojo en un clon con el aviso
  «no se pudo comprobar». Las otras quince se ejecutan sobre lo publicado.
- La empresa es ficticia y los datos son sintéticos.
- La web está en español.

## Cómo está hecho

Con ayuda de IA. Las decisiones y la revisión de cada página son mías. Claude, de Anthropic, escribió buena
parte del análisis, del código y del texto bajo esa revisión. Los verificadores que recalcularon las cifras
también son agentes de IA, con la instrucción de no fiarse de los scripts del proyecto.

La web se publica en Vercel desde la carpeta `web` de la rama `main`: cada cambio que llega a `main` la vuelve a
construir.

## Repositorios relacionados

- [RFM-Customer-Analytics](https://github.com/jleonceo/RFM-Customer-Analytics): segmentación de clientes por
  recencia, frecuencia e importe, el caso en que el fichero sí identifica al cliente.
- [lead-scoring-ml](https://github.com/jleonceo/lead-scoring-ml): ordenar contactos comerciales por su
  probabilidad de compra.
- [accident-intelligent-agent](https://github.com/jleonceo/accident-intelligent-agent): accidentes de tráfico en
  Madrid en 2020, de los datos abiertos del Ayuntamiento a un modelo que estima quién necesitará asistencia
  sanitaria.
- [analisis-contable](https://github.com/jleonceo/analisis-contable): cuenta de resultados y tesorería de 2024
  con pandas, comprobadas por un segundo camino.
- [tesoreria-forecast-ia](https://github.com/jleonceo/tesoreria-forecast-ia): previsión de caja medida contra el
  pasado.

---

*Parte del portfolio de [Juan Luis León](https://github.com/jleonceo) · [juanluisleon.vercel.app](https://juanluisleon.vercel.app) · Licencia [MIT](LICENSE)*
