// Identidad y navegación del sitio. Caso ficticio: TechSoluciones S.L.
// Las cifras de las descripciones se leen de los JSON, con la misma expresión que el título de su
// página, para que el menú no se quede atrás si un script cambia (23/09/2026).
import ak from './atipicos_kpi.json';
import eda from './eda.json';
import inf from './inferencia.json';
import seg from './segmentacion.json';

const f = (v, n = 0) => new Intl.NumberFormat('es-ES', { minimumFractionDigits: n, maximumFractionDigits: n, useGrouping: true }).format(v);
const salto = ak.d12_denominador.mayores_saltos[0];
const bosque = ak.e6_tasas.detectores.find((x) => x.detector === 'isolationforest');
const corr = eda.p3_correlacion_ventas_satisfaccion.cant_vs_satisfaccion_pearson;
const simp = inf.f9_simpson;
const emp = inf.f15_emparejamiento;
const mult = inf.f11_comparaciones_multiples;
const marg = inf.f10_margen_kpi;
const part = seg.h5_particion.por_semilla[0];
const fuga = seg.h7_h10_fuga_e_importancia.con_fuga;

export const marca = {
  nombre: 'TechSoluciones',
  nombreAcento: ' Analytics',
  titulo: 'De datos sucios a decisiones · TechSoluciones S.L.',
  descripcion:
    'Recorrido completo de analítica de datos: inspección, limpieza, anonimización, EDA, machine learning y cuadro de mando, con método y rigor. Cada paso, explicado.',
};

// Estructura pedagógica: 8 partes, en orden.
export const partes = [
  { id: 'inicio', titulo: '', items: [{ slug: '/', t: 'Portada' }] },
  {
    id: 'I', titulo: 'I · El problema y los datos',
    items: [
      { slug: '/contexto', t: '1 · Contexto y misión' },
      { slug: '/inspeccion', t: '2 · Primer contacto con los datos' },
      { slug: '/calidad-datos', t: '3 · Teoría de la calidad de datos' },
    ],
  },
  {
    id: 'II', titulo: 'II · Preparación',
    items: [
      { slug: '/etl', t: '4 · Limpieza y estandarización' },
      { slug: '/diccionario', t: '5 · Diccionario de datos' },
      { slug: '/anonimizacion', t: '6 · PII y anonimización' },
    ],
  },
  {
    id: 'III', titulo: 'III · Análisis exploratorio',
    items: [
      {
        slug: '/descriptiva',
        t: '7 · Estadística descriptiva',
        sub: [
          { slug: '/descriptiva/nivel-agregacion', t: 'El nivel de agregación', ficha: 'D6' , d: 'La misma pregunta cambia de ganador según se mida por venta o por periodo' },
          { slug: '/descriptiva/denominador', t: 'El denominador olvidado', ficha: 'D12' , d: `${salto.reg} es la ${salto.puesto_por_total}.ª provincia por facturación y la ${salto.puesto_por_venta}.ª por venta` },
          { slug: '/descriptiva/forma', t: 'La forma de una variable', ficha: 'D3', d: 'Unas pocas ventas muy grandes alargan el reparto del importe; la cantidad se reparte por igual' },
          { slug: '/descriptiva/media-mediana', t: 'Media frente a mediana', ficha: 'D11', d: 'La mayoría de las ventas queda por debajo de la venta media' },
          { slug: '/descriptiva/pareto', t: 'El 80/20 no es una ley', ficha: 'D4', d: 'La facturación se concentra en pocos productos y se reparte entre las provincias' },
          { slug: '/descriptiva/grafico', t: 'Qué gráfico para qué pregunta', ficha: 'D8', d: 'El tipo de gráfico se elige según la conclusión que tiene que mostrar' },
          { slug: '/descriptiva/fases', t: 'El EDA por fases', ficha: 'D9', d: 'Este mismo recorrido, puesto en el orden que exige el método' },
        ],
      },
      {
        slug: '/atipicos',
        t: '8 · Atípicos y anomalías',
        sub: [
          { slug: '/atipicos/z-score', t: 'Atípico por z-score', ficha: 'E2' , d: 'Los atípicos aumentan la desviación con la que el z-score intenta detectarlos' },
          { slug: '/atipicos/clases', t: 'Las tres clases de anomalía', ficha: 'E9' , d: 'Una venta normal en el total puede ser rara en su provincia, y un mes puede salirse sin que lo sea ninguna venta' },
          { slug: '/atipicos/alertas', t: 'Calibrar una alerta', ficha: 'E8' , d: 'Con el umbral más bajo, casi todos los avisos son falsos' },
          { slug: '/atipicos/lof-dbscan', t: 'LOF y DBSCAN', ficha: 'E11' , d: 'Los dos encuentran las anomalías de la muestra y el parámetro decide cuántas más marcan' },
          { slug: '/atipicos/falsos-positivos', t: 'Cuánto se equivoca un detector', ficha: 'E6', d: `Un ${f(bosque.tasa_falsos_positivos_pct, 1)} % de falsas alarmas que son ${f(100 - bosque.precision_pct, 0)} de cada 100 avisos` },
        ],
      },
      { slug: '/series', t: '9 · Series y estacionalidad' },
      { slug: '/segmentos', t: '10 · Producto, categoría, región' },
    ],
  },
  {
    id: 'IV', titulo: 'IV · Las preguntas de negocio',
    items: [
      { slug: '/pregunta-mes', t: '11 · ¿El mes de mayores ventas?' },
      { slug: '/pregunta-region', t: '12 · ¿Qué región crece en satisfacción?' },
      { slug: '/pregunta-correlacion', t: '13 · ¿Ventas y satisfacción se relacionan?' },
      {
        slug: '/senal-ruido',
        t: '14 · La lección: señal frente a ruido',
        sub: [
          { slug: '/senal-ruido/simpson', t: 'La paradoja de Simpson', ficha: 'F9', d: 'La provincia que más factura por venta debe su ventaja a qué productos vende' },
          { slug: '/senal-ruido/doce-meses', t: 'El ganador de doce meses', ficha: 'F7', d: 'Entre doce meses siempre hay uno primero y hay que compararlo con el mejor mes del azar' },
          { slug: '/senal-ruido/tamano-efecto', t: 'Significativo no es importante', ficha: 'F6', d: `Una relación con p = ${f(corr.p, 3)} que explica el ${f(100 * corr.r * corr.r, 2)} % de la satisfacción` },
          { slug: '/senal-ruido/emparejamiento', t: 'Emparejar antes de comparar', ficha: 'F15', d: `Al comparar el mismo producto, casi toda la ventaja de ${f(emp.diferencia_bruta)} € desaparece` },
          { slug: '/senal-ruido/comparaciones-multiples', t: 'Comparaciones múltiples', ficha: 'F11', d: `Salen ${mult.significativos_sin_corregir} provincias especiales cuando el azar ya daba ${f(mult.esperados_por_azar, 1)}` },
          { slug: '/senal-ruido/intervalo-confianza', t: 'El intervalo de confianza', ficha: 'F5', d: 'Un promedio necesita su margen de error para poder compararlo' },
          { slug: '/senal-ruido/margen-kpi', t: 'El margen de un KPI', ficha: 'F10', d: `La facturación media mensual se conoce con un margen de ${f((marg.ic95_alto - marg.ic95_bajo) / 2)} € arriba o abajo` },
          { slug: '/senal-ruido/potencia', t: 'Potencia estadística', ficha: 'F8', d: 'Un «no hay diferencia» puede deberse a que no había datos suficientes para detectarla' },
          { slug: '/senal-ruido/bootstrap-vs-normal', t: 'Bootstrap frente a fórmula', ficha: 'F12', d: 'La fórmula de la distribución normal da el mismo intervalo aunque el importe no sea normal' },
          { slug: '/senal-ruido/correlacion-parcial', t: 'Correlación parcial', ficha: 'F13', d: 'Descontar el efecto del producto tampoco hace aparecer una relación' },
          { slug: '/senal-ruido/sesgo-seleccion', t: 'Quién contesta la encuesta', ficha: 'F14', d: 'Una de cada cinco ventas no tiene satisfacción y hay que saber por qué' },
        ],
      },
    ],
  },
  {
    id: 'V', titulo: 'V · Machine Learning',
    items: [
      {
        slug: '/segmentacion',
        t: '15 · ¿Se pueden segmentar los clientes?',
        sub: [
          { slug: '/segmentacion/rfm', t: 'RFM: primero, saber quién es el cliente', ficha: 'H1' , d: 'El correo parece la clave y lo comparten personas distintas' },
          { slug: '/segmentacion/elegir-k', t: 'Cuántos grupos hay', ficha: 'H2' , d: 'La inercia baja siempre, así que por sí sola no dice cuántos grupos elegir' },
          { slug: '/segmentacion/escalado', t: 'Escalar antes de agrupar', ficha: 'H8' , d: 'Sin escalar, el importe en euros domina a las otras dos variables' },
          { slug: '/segmentacion/dimensionalidad', t: 'La maldición de la dimensionalidad', ficha: 'H12' , d: `Con cincuenta columnas de ruido, el contraste entre distancias cae un ${f(seg.h12_dimensionalidad.caida_contraste, 1)} %` },
          { slug: '/segmentacion/mezclas', t: 'Mezclas gaussianas', ficha: 'H14' , d: 'Asigna cada punto con una probabilidad y aquí casi nunca duda' },
        ],
      },
      {
        slug: '/prediccion',
        t: '16 · ¿Se puede predecir? Y las anomalías',
        sub: [
          { slug: '/prediccion/particion', t: 'Entrenar y probar por separado', ficha: 'H5', d: `Medido con los datos con los que aprendió, un modelo sin señal saca un ${f(part.r2_entrenamiento, 2)}` },
          { slug: '/prediccion/fuga', t: 'Fuga de información', ficha: 'H7' , d: `Un R² de ${f(fuga.r2_prueba, 4)} indica que la respuesta se ha colado entre las variables` },
          { slug: '/prediccion/elegir-algoritmo', t: 'Cómo se elige un algoritmo', ficha: 'H9', d: 'Dos modelos empatan con predecir la media y gana el más simple' },
        ],
      },
    ],
  },
  {
    id: 'VI', titulo: 'VI · Cuadro de mando y negocio',
    items: [
      {
        slug: '/cuadro-mando',
        t: '17 · Cuadro de mando',
        sub: [
          { slug: '/cuadro-mando/que-va-arriba', t: 'Qué va arriba en el panel', ficha: 'J5', d: 'Arriba lo que obliga a decidir algo, abajo lo que lo explica' },
          { slug: '/cuadro-mando/kpi-vanidad', t: 'KPI frente a vanidad', ficha: 'J1', d: 'Una cifra que solo puede subir no sirve para avisar de un problema' },
          { slug: '/cuadro-mando/mapa-kpis', t: 'Mapa de KPIs y North Star', ficha: 'J2', d: 'De diez KPIs habituales, con esta tabla solo se pueden calcular tres' },
          { slug: '/cuadro-mando/mapa', t: 'El mapa por provincia', ficha: 'J9', d: `Con ${ak.j9_mapa.n_provincias} provincias, la magnitud elegida decide qué se ve` },
          { slug: '/cuadro-mando/dax', t: 'La medida DAX y su gemela en script', ficha: 'J7', d: 'La misma cifra, calculada por dos caminos independientes' },
          { slug: '/cuadro-mando/narrativa', t: 'La narrativa automática', ficha: 'J8', d: 'Tres frases que escribiría un resumen automático del panel y que no superan la comprobación' },
          { slug: '/cuadro-mando/escalera', t: 'La escalera de la analítica', ficha: 'J3', d: 'Qué pasó, por qué, qué pasará y qué hacer. Aquí falla el tercer peldaño' },
          { slug: '/cuadro-mando/recomendacion', t: 'Anatomía de una recomendación', ficha: 'J4', d: 'Entre los datos y la IA hace falta el contexto, que evita que la IA invente' },
        ],
      },
      { slug: '/recomendaciones', t: '18 · Recomendaciones de negocio' },
    ],
  },
  {
    id: 'VII', titulo: 'VII · Cómo se hizo',
    items: [
      { slug: '/metodologia', t: '19 · Metodología y determinismo' },
      { slug: '/conclusiones', t: '20 · Conclusiones y siguientes pasos' },
      { slug: '/ecosistema', t: 'Ecosistema y créditos' },
    ],
  },
  {
    id: 'VIII', titulo: 'VIII · Consulta y repaso',
    items: [
      { slug: '/glosario', t: '21 · Glosario' },
      { slug: '/repaso', t: '22 · Preguntas de repaso' },
    ],
  },
];

// Orden plano para navegación anterior/siguiente.
export const orden = partes.flatMap((p) => p.items.flatMap((it) => [it, ...(it.sub || [])]));

export function vecinos(slug) {
  const i = orden.findIndex((x) => x.slug === slug);
  return {
    prev: i > 0 ? orden[i - 1] : null,
    next: i >= 0 && i < orden.length - 1 ? orden[i + 1] : null,
  };
}
