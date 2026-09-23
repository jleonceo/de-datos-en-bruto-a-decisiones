# de-datos-sucios-a-decisiones

**Un fichero de ventas sucio, llevado paso a paso hasta las preguntas de la dirección, con cada cifra comprobada**
**A dirty sales file taken step by step to management's questions, with every figure checked**

[Español](#español) · [English](#english)

Web: https://de-datos-sucios-a-decisiones.vercel.app

---

## Español

### El problema

Una pyme tiene ocho años de ventas en un fichero y tres preguntas: qué mes vende más, qué provincia
mejora más en satisfacción y si la satisfacción acompaña a las ventas. El fichero trae fechas en cuatro
formatos, productos escritos de dos maneras, 827 filas duplicadas y 16 ventas imposibles.

Con ese fichero se puede montar un cuadro de mando en una tarde, y casi todo lo que enseñaría sería
ruido.

Este repositorio hace el recorrido completo: inspeccionar, limpiar, anonimizar, explorar,
contrastar con estadística y decidir qué va en el cuadro de mando. Lo cuenta en una web de 63 páginas
pensada para quien no es del gremio.

### El ejemplo

La empresa, TechSoluciones S.L., es ficticia. Los datos son sintéticos. Las respuestas a sus tres
preguntas:

| Pregunta | Qué dicen los datos |
|---|---|
| ¿Qué mes vende más? | Octubre de 2023, con 709.580 €. Agosto tiene la media más alta de los doce meses, un 4,49 % por encima, pero barajando los datos el azar produce un ganador así en el 87 % de los casos |
| ¿Qué provincia mejora más en satisfacción? | Navarra, pero el azar da una pendiente igual o mayor en 60 de cada 100 barajados. Quitando 2026, que está incompleto, la primera pasa a ser Madrid |
| ¿La satisfacción acompaña a las ventas? | No. La correlación entre importe y satisfacción es de 0,0034 sobre 15.980 ventas |

Las tres respuestas acaban en lo mismo: con estos datos no se puede concluir lo que la pregunta daba
por hecho. La web explica por qué y se detiene en los casos en que una cifra parece un hallazgo y es
ruido: el mes que gana entre doce, la provincia que destaca entre 52, el ticket medio que depende de
qué productos se venden.

Tampoco se pueden segmentar clientes. El fichero no trae un código de cliente, 5.035 correos los usan
personas con nombre distinto y, contando por nombre y teléfono, nadie compra dos veces.

### Cómo se comprobó

Ninguna cifra de la web la calcula un modelo de lenguaje. Salen de diez scripts de Python con semilla
fija. Escriben sus resultados en ficheros JSON y la web los lee de ahí. Antes de publicar, tres verificadores recalcularon desde el fichero original, con código propio,
1.439 cifras de las páginas. Cuadraron 1.423. Ocho no cuadraban por redondeos o por cómo las leía la
página. Se corrigieron. Otras tres son un mismo p de 0,60 que con más barajados sale 0,62, sin
cambiar la conclusión. Las cinco restantes no son medidas del dato. Un revisor intentó refutar 51
conclusiones: se sostuvieron 23, se matizaron 23 y se corrigieron las cinco que caían.

El banco `analisis/verificar_correcciones.py` guarda 19 comprobaciones de errores que ya se
cometieron una vez, entre ellas que ningún fichero publicado lleve un nombre, un correo o un teléfono.

### Lo que no se puede reproducir desde aquí

El primer script lee el fichero original, que no se publica porque contiene datos personales:
nombres, correos y teléfonos, aunque sean inventados. En este repositorio están los scripts, sus
resultados y el fichero anonimizado, que solo lleva año, provincia, satisfacción y la marca de
anomalía. Con él no se puede ejecutar la cadena de scripts. Por la misma razón, cuatro comprobaciones del banco (C1, C2, C7 y C16) salen en rojo en un clon con
el aviso «no se pudo comprobar»: leen el fichero original, el limpio o el anonimizado interno, que
no se publican. Las otras quince se ejecutan
sobre lo publicado.

### Qué hay en este repositorio

```
web/                   la web, hecha con Astro, Tailwind y daisyUI
  src/pages/           las 63 páginas
  src/data/            los JSON que leen las páginas, copiados de analisis/salidas
analisis/              los diez scripts, en el orden en que se ejecutan
  salidas/             sus resultados
  verificar_correcciones.py   el banco de comprobaciones
data/                  el fichero anonimizado que se puede publicar
INFORME_TECNICO.md     el informe técnico completo, con las decisiones de cada paso
```

### Ver la web en local

```bash
cd web
npm install
npm run dev
```

Hace falta Node 22.12 o posterior. `npm run build` genera la web estática en `web/dist`.

### Cómo se publica

La web está en Vercel, conectada a este repositorio de GitHub. Vercel construye la carpeta `web` con
`npm run build` y publica `web/dist`. Cada cambio que llega a la rama `main` vuelve a publicar la web
sin pasos a mano. Un cambio en otra rama o en una pull request genera su propia
dirección de prueba, así que se puede revisar antes de que llegue a la web principal.

Si un script cambia sus resultados, el orden es: ejecutar la cadena en la carpeta de trabajo, copiar
los JSON de `analisis/salidas` a `web/src/data`, pasar el banco y subir los cambios.

### Cómo está hecho

Con ayuda de IA. Las decisiones y la revisión de cada página son mías. Claude, de Anthropic, ha
escrito buena parte del análisis, del código y del texto bajo esa revisión, y los verificadores que
recalcularon las cifras también son agentes de IA, con la instrucción de no fiarse de los scripts del
proyecto.

### Ecosistema

- **[RFM-Customer-Analytics](https://github.com/jleonceo/RFM-Customer-Analytics)**, segmentación RFM de clientes. Aquí la misma técnica no se puede aplicar; la web explica por qué.
- **[lead-scoring-ml](https://github.com/jleonceo/lead-scoring-ml)**, un modelo que predice qué contactos van a comprar.
- **[control-interno-fraude-ia](https://github.com/jleonceo/control-interno-fraude-ia)**, detección de anomalías contables con aritmética. Aquí las anomalías son ventas imposibles.
- **[pii-output-gate](https://github.com/jleonceo/pii-output-gate)**, una puerta que bloquea los datos personales antes de que salgan. Aquí se anonimiza el fichero antes de publicarlo.
- **[verificacion-determinista-ia](https://github.com/jleonceo/verificacion-determinista-ia)**, comprobaciones de coherencia sin IA, el mismo principio que el banco de este repositorio.
- **[analisis-contable](https://github.com/jleonceo/analisis-contable)**, análisis financiero con Python y MySQL sobre otra empresa ficticia.

### Licencia

MIT. Los datos son sintéticos y la empresa es ficticia.

---

## English

### The problem

A small company has eight years of sales in one file and three questions: which month sells most,
which province improves most in customer satisfaction, and whether satisfaction goes along with
sales. The file has dates in four formats, products spelled two ways, 827 duplicated rows and 16
impossible sales.

With that file you can build a dashboard in an afternoon, and almost everything it showed would be
noise.

This repository does the whole journey: inspect, clean, anonymise, explore, test with
statistics and decide what goes on the dashboard. It tells the story in a 63-page website written
for readers outside the field. The website is in Spanish.

### The example

The company is fictitious, TechSoluciones S.L., and the data are synthetic. The answers to its three
questions:

| Question | What the data say |
|---|---|
| Which month sells most? | October 2023, with €709,580. August has the highest average of the twelve months, 4.49% above, but shuffling the data, chance produces a winner like that 87% of the time |
| Which province improves most in satisfaction? | Navarra, but chance gives an equal or steeper slope in 60 out of 100 shuffles. Leaving out 2026, which is incomplete, the top province becomes Madrid |
| Does satisfaction go along with sales? | No. The correlation between amount and satisfaction is 0.0034 over 15,980 sales |

The three answers end in the same place: with these data you cannot conclude what the question took
for granted. The website explains why, and stops at the cases where a figure looks like a finding and
is noise: the month that wins among twelve, the province that stands out among 52, the average ticket
that depends on which products are sold.

Customers cannot be segmented either. The file has no customer code, 5,035 email addresses are used by
people with different names and, counting by name and phone, nobody buys twice.

### How it was checked

No figure on the website is calculated by a language model. They come from ten Python scripts with a
fixed seed, which write their results to JSON files, and the website reads them from there. Before
publishing, three verifiers recalculated 1,439 figures on the pages from the original file,
with their own code. 1,423 matched. Eight did not match because of rounding or because of how the page
read them, and they were corrected. Another three are the same p of 0.60, which comes out at 0.62
with more shuffles without changing the conclusion. The remaining five are not measurements of the
data. A reviewer tried to refute 51 conclusions: 23 held, 23 were qualified and the five that fell
were corrected.

The test bench `analisis/verificar_correcciones.py` keeps 19 checks for errors that were already made
once, including that no published file contains a name, an email or a phone number.

### What cannot be reproduced from here

The first script reads the original file, which is not published because it contains personal data:
names, emails and phone numbers, even though they are made up. This repository holds the scripts,
their results and the anonymised file, which only has year, province, satisfaction and the anomaly
flag. The script chain cannot be run with it. For the same reason, four checks in the bench (C1, C2, C7 and C16) show red in a clone with the
message «no se pudo comprobar» (could not be checked): they read the original, the cleaned or the
internal anonymised file, none of which is published. The
other fifteen run on what is published.

### What is in this repository

```
web/                   the website, built with Astro, Tailwind and daisyUI
  src/pages/           the 63 pages
  src/data/            the JSON files the pages read, copied from analisis/salidas
analisis/              the ten scripts, in the order they run
  salidas/             their results
  verificar_correcciones.py   the test bench
data/                  the anonymised file that can be published
INFORME_TECNICO.md     the full technical report, with the decisions at each step (in Spanish)
```

### Run the website locally

```bash
cd web
npm install
npm run dev
```

It needs Node 22.12 or later. `npm run build` generates the static site in `web/dist`.

### How it is published

The website is on Vercel, connected to this GitHub repository. Vercel builds the `web` folder with
`npm run build` and publishes `web/dist`. Every change that reaches the `main` branch republishes the
site with no manual steps. A change on another branch or in a pull request gets
its own preview address, so it can be reviewed before it reaches the main site.

If a script changes its results, the order is: run the chain in the working folder, copy the JSON
files from `analisis/salidas` to `web/src/data`, run the bench and push the changes.

### How it was made

With the help of AI. The decisions and the review of every page are mine. Claude, by Anthropic, wrote
a good part of the analysis, the code and the text under that review, and the verifiers that
recalculated the figures are also AI agents, instructed not to trust the project's scripts.

### Ecosystem

- **[RFM-Customer-Analytics](https://github.com/jleonceo/RFM-Customer-Analytics)**, RFM customer segmentation. Here the same technique cannot be applied, and the website explains why.
- **[lead-scoring-ml](https://github.com/jleonceo/lead-scoring-ml)**, a model that predicts which leads will buy.
- **[control-interno-fraude-ia](https://github.com/jleonceo/control-interno-fraude-ia)**, detecting accounting anomalies with arithmetic. Here the anomalies are impossible sales.
- **[pii-output-gate](https://github.com/jleonceo/pii-output-gate)**, a gate that blocks personal data before it leaves. Here the file is anonymised before it is published.
- **[verificacion-determinista-ia](https://github.com/jleonceo/verificacion-determinista-ia)**, coherence checks without AI, the same principle as this repository's bench.
- **[analisis-contable](https://github.com/jleonceo/analisis-contable)**, financial analysis with Python and MySQL on another fictitious company.

### License

MIT. The data are synthetic and the company is fictitious.
