(function (global) {
  "use strict";

  const NOMBRES = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"];
  const SEMITONOS = [0, 2, 4, 5, 7, 9, 11];
  const BASE_CLAVE = { sol: 4 * 7 + 2, fa: 2 * 7 + 4 };

  function crearPentagrama(yCentro, sep) {
    const yInferior = yCentro + 2 * sep;
    return {
      sep: sep,
      yInferior: yInferior,
      posicion: (y) => Math.round((yInferior - y) / (sep / 2)),
      yDePosicion: (pos) => yInferior - (pos * sep) / 2,
    };
  }

  function nota(pos, clave, alteracion) {
    const d = BASE_CLAVE[clave] + pos;
    const octava = Math.floor(d / 7);
    const paso = ((d % 7) + 7) % 7;
    const midi = 12 * (octava + 1) + SEMITONOS[paso] + alteracion;
    const signo = alteracion > 0 ? "♯" : alteracion < 0 ? "♭" : "";
    return { midi: midi, nombre: NOMBRES[paso] + signo + octava };
  }

  function cabezaY(r, sep) {
    const filas = new Float64Array(r.alto);
    for (let y = 0; y < r.alto; y++) {
      let s = 0;
      for (let x = 0; x < r.ancho; x++) s += r.alfa[y * r.ancho + x];
      filas[y] = s / 255;
    }
    const centro = (a, b, potencia) => {
      let num = 0, den = 0;
      for (let y = a; y < b; y++) { const w = Math.pow(filas[y], potencia); num += w * y; den += w; }
      return den > 0 ? num / den : (a + b) / 2;
    };
    if (r.alto < 1.9 * sep) return r.y0 + centro(0, r.alto, 1);

    const franja = Math.round(1.3 * sep);
    let arriba = 0, abajo = 0;
    for (let y = 0; y < franja; y++) arriba += filas[y];
    for (let y = r.alto - franja; y < r.alto; y++) abajo += filas[y];
    return arriba > abajo ? r.y0 + centro(0, franja, 2) : r.y0 + centro(r.alto - franja, r.alto, 2);
  }

  function interpretar(simbolos, pentagrama, umbral) {
    let clave = "sol";
    let alteracion = 0;
    const eventos = [];
    simbolos.forEach((s, i) => {
      s.nota = null;
      s.valido = s.clase !== null && s.conf >= umbral;
      if (!s.valido) return;
      const c = s.clase;
      if (c.tipo === "clave") {
        clave = c.carpeta === "clave_fa" ? "fa" : "sol";
        s.detalle = "Clave de " + clave;
      } else if (c.tipo === "alteracion") {
        alteracion = c.carpeta === "sostenido" ? +1 : -1;
        s.detalle = alteracion > 0 ? "+½ tono a la siguiente" : "−½ tono a la siguiente";
      } else if (c.tipo === "silencio") {
        s.detalle = c.duracion + (c.duracion === 1 ? " tiempo" : " tiempos");
        eventos.push({ indice: i, midi: null, tiempos: c.duracion });
      } else {
        s.posicion = pentagrama.posicion(s.cabezaY);
        s.nota = nota(s.posicion, clave, alteracion);
        s.detalle = s.nota.nombre;
        eventos.push({ indice: i, midi: s.nota.midi, tiempos: c.duracion });
        alteracion = 0;
      }
    });
    return eventos;
  }

  global.Pentagrama = { crearPentagrama, nota, cabezaY, interpretar };
})(window);
