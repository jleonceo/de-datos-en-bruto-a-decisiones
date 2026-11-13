// Mapa del sitio. Sale del mismo orden de páginas que usa el menú, así que no se queda atrás.
import { orden } from '../data/site.js';

export function GET({ site }) {
  const urls = orden
    .map((p) => `  <url><loc>${new URL(p.slug, site).href}</loc></url>`)
    .join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
