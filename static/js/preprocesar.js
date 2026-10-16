(function (global) {
  "use strict";
  const TAM = 32, UMBRAL_TINTA = 10, MARGEN_PCT = 12;

  function preprocesarAlfa(alfa, ancho, alto) {
    let y0 = Infinity, y1 = -1, x0 = Infinity, x1 = -1;
    for (let y = 0; y < alto; y++) {
      for (let x = 0; x < ancho; x++) {
        if (alfa[y * ancho + x] > UMBRAL_TINTA) {
          if (y < y0) y0 = y; if (y > y1) y1 = y;
          if (x < x0) x0 = x; if (x > x1) x1 = x;
        }
      }
    }
    const salida = new Float32Array(TAM * TAM);
    if (y1 < 0) return salida;
    y1 += 1; x1 += 1;
    const h = y1 - y0, w = x1 - x0;
    const lado = Math.max(h, w);
    const ladoMargen = lado + 2 * Math.max(2, Math.floor((lado * MARGEN_PCT) / 100));
    const k = Math.max(1, Math.ceil(ladoMargen / TAM));
    const ladoFinal = TAM * k;
    const oy = Math.floor((ladoFinal - h) / 2);
    const ox = Math.floor((ladoFinal - w) / 2);

    const suma = new Float64Array(TAM * TAM);
    for (let y = 0; y < h; y++) {
      const by = Math.floor((y + oy) / k);
      for (let x = 0; x < w; x++) {
        const v = alfa[(y + y0) * ancho + (x + x0)];
        if (v) suma[by * TAM + Math.floor((x + ox) / k)] += v;
      }
    }
    const div = k * k * 255;
    for (let i = 0; i < suma.length; i++) salida[i] = suma[i] / div;
    return salida;
  }

  global.preprocesarAlfa = preprocesarAlfa;
  if (typeof module !== "undefined") module.exports = { preprocesarAlfa };
})(typeof window !== "undefined" ? window : globalThis);
