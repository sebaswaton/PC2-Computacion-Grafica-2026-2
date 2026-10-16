(function (global) {
  "use strict";

  function segmentar(trazos, grosor, margen) {
    const items = trazos
      .map((t) => ({ t: t, caja: cajaDeTrazo(t, grosor) }))
      .sort((a, b) => a.caja.minX - b.caja.minX);

    const grupos = [];
    for (const it of items) {
      const g = grupos[grupos.length - 1];
      if (g && it.caja.minX <= g.caja.maxX + margen) {
        g.trazos.push(it.t);
        g.caja.minX = Math.min(g.caja.minX, it.caja.minX);
        g.caja.minY = Math.min(g.caja.minY, it.caja.minY);
        g.caja.maxX = Math.max(g.caja.maxX, it.caja.maxX);
        g.caja.maxY = Math.max(g.caja.maxY, it.caja.maxY);
      } else {
        grupos.push({ trazos: [it.t], caja: Object.assign({}, it.caja) });
      }
    }
    return grupos;
  }

  function rasterizarGrupo(grupo, grosor) {
    const x0 = Math.floor(grupo.caja.minX) - 2;
    const y0 = Math.floor(grupo.caja.minY) - 2;
    const ancho = Math.ceil(grupo.caja.maxX) + 2 - x0;
    const alto = Math.ceil(grupo.caja.maxY) + 2 - y0;
    const c = document.createElement("canvas");
    c.width = ancho; c.height = alto;
    const ctx = c.getContext("2d", { willReadFrequently: true });
    dibujarTrazos(ctx, grupo.trazos, grosor, "#000", -x0, -y0);
    const rgba = ctx.getImageData(0, 0, ancho, alto).data;
    const alfa = new Uint8ClampedArray(ancho * alto);
    for (let i = 0; i < alfa.length; i++) alfa[i] = rgba[i * 4 + 3];
    return { alfa: alfa, ancho: ancho, alto: alto, x0: x0, y0: y0 };
  }

  global.segmentar = segmentar;
  global.rasterizarGrupo = rasterizarGrupo;
})(window);
