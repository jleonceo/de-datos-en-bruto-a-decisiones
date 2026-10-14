Versión en español: [README.md](README.md)

# Sales: from a raw file to a dashboard

A complete analysis of a raw sales file to answer three business questions: which month sells most, which
province improves most in customer satisfaction and whether satisfaction goes along with sales. It covers
cleaning, anonymisation, exploratory analysis, statistical testing and dashboard design, and tells the story in
a 63-page website, written in Spanish.

**Result:** none of the three questions has the answer it took for granted. The best month, the most improved
province and the link between satisfaction and amount cannot be told apart from chance with these data. Every
figure on the website was recalculated from the original file before publishing.

Website: [de-datos-en-bruto-a-decisiones.vercel.app](https://de-datos-en-bruto-a-decisiones.vercel.app)

```bash
cd web
npm install
npm run dev
```

It needs Node 22.12 or later. `npm run build` generates the static site in `web/dist`.

## The starting problem

A fictitious small company, TechSoluciones S.L., has its sales from 2019 to May 2026 in one file. It has dates in
four formats, products spelled two ways, 827 duplicated rows and 16 impossible sales. A dashboard can be built
from that file in an afternoon, but almost everything it showed would be noise.

## What comes out

| Question | What the data say |
|---|---|
| Which month sells most? | October 2023, with 709,580 €. August has the highest average, 4.49 % above, but shuffling the data, chance produces a winner like that 87 % of the time |
| Which province improves most in satisfaction? | Navarra, although chance gives an equal or larger improvement in 60 out of 100 shuffles. Without 2026, which is incomplete, it becomes Madrid |
| Does satisfaction go along with sales? | No. The correlation between amount and satisfaction is 0.0034 over 15,980 sales |

Customers cannot be segmented either: the file has no customer code, 5,035 email addresses are used by people
with different names and, counting by name and phone, nobody buys twice.

## What is inside

1. `analisis/` holds the ten Python scripts, in the order they run: profiling, cleaning, dictionary,
   anonymisation, exploratory analysis, robustness, models, inference, segmentation and outliers.
2. `analisis/salidas/` keeps their results in JSON, which is what the website reads.
3. `analisis/verificar_correcciones.py` repeats 19 checks for errors that were already made once, including that
   no published file contains a name, an email or a phone number.
4. `web/` is the website, built with Astro, Tailwind and daisyUI. Each concept has its own page: the problem, why
   it misleads, the solution and what happens with these data.
5. `data/` holds the anonymised file that can be published.
6. `INFORME_TECNICO.md` is the full technical report, with the decisions at each step, in Spanish.

## How it was checked

No language model calculates the figures on the website: they come from the scripts, with a fixed seed.
Before publishing, three verifiers recalculated 1,439 figures on the pages from the original file, with their own
code. Those that did not match because of rounding or because of how the page read them were corrected. A
reviewer tried to refute 51 conclusions. Five did not hold and were corrected.

## Limits

- The original file is not published because it contains names, emails and phone numbers, even though they are
  made up. With the anonymised file, which only has year, province, satisfaction and the anomaly flag, the script
  chain cannot be run.
- For the same reason, four of the 19 checks (C1, C2, C7 and C16) show red in a clone with the message «no se pudo
  comprobar» (could not be checked). The other fifteen run on what is published.
- The company is fictitious and the data are synthetic.
- The website is in Spanish.

## How it was made

With the help of AI. The decisions and the review of every page are mine. Claude, by Anthropic, wrote a good
part of the analysis, the code and the text under that review. The verifiers that recalculated the figures are
also AI agents, instructed not to trust the project's scripts.

The website is published on Vercel from the `web` folder of the `main` branch: every change that reaches `main`
rebuilds it.

## Related repositories

- [RFM-Customer-Analytics](https://github.com/jleonceo/RFM-Customer-Analytics): customer segmentation by recency,
  frequency and monetary value, the case where the file does identify the customer.
- [lead-scoring-ml](https://github.com/jleonceo/lead-scoring-ml): ranking sales contacts by their probability of
  buying.
- [accident-intelligent-agent](https://github.com/jleonceo/accident-intelligent-agent): road accidents in Madrid in
  2020, from the City Council's open data to a model that estimates who will need medical assistance.
- [analisis-contable](https://github.com/jleonceo/analisis-contable): 2024 income statement and cash with pandas,
  checked by a second route.
- [tesoreria-forecast-ia](https://github.com/jleonceo/tesoreria-forecast-ia): cash forecast tested against the
  past.

---

*Part of [Juan Luis León](https://github.com/jleonceo)'s portfolio · [juanluisleon.vercel.app](https://juanluisleon.vercel.app) · Licence [MIT](LICENSE)*
