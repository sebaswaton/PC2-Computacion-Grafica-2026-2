(function () {
  "use strict";
  const C = window.CONFIG;
  const $ = (id) => document.getElementById(id);

  const ANCHO = 1200, ALTO = 320, Y_CENTRO = 160, SEP = C.separacion;
  const MARGEN_SEGMENTACION = SEP * 0.5;
  const COLORES = { azul: "#2D4F9E", alerta: "#B4233C", tinta: "#1A2238", suave: "#5A6480", resalte: "rgba(45,79,158,0.13)" };

  const pentagrama = Pentagrama.crearPentagrama(Y_CENTRO, SEP);
  dibujarPentagrama($("pauta"), Y_CENTRO, SEP, "#A9B8D6", 16, ANCHO - 16);

  const anot = $("anotaciones").getContext("2d");
  const reproductor = new Reproductor();
  let modelo = null;
  let simbolos = [];
  let eventos = [];
  let sonando = null;
  let seleccionado = null;
  let temporizador = null;

  const lienzo = new LienzoTrazos($("dibujo"), {
    grosor: C.grosor,
    alCambiar: () => {
      clearTimeout(temporizador);
      temporizador = setTimeout(reconocer, 250);
    },
  });

  function mostrarEstadoModelo(texto, clase) {
    const e = $("estado-modelo");
    e.textContent = texto; e.className = "estado-modelo " + clase; e.hidden = false;
  }

  cargarModelo("/static/modelo/")
    .then((m) => {
      modelo = m;
      const i = m.info;
      $("info-modelo").textContent =
        `Modelo: ${i.arquitectura.toUpperCase()} · exactitud en prueba ${(100 * i.exactitud_prueba).toFixed(1)} % · ${i.fecha}`;
      if (i.origen === "sintetico") {
        mostrarEstadoModelo("Este es el modelo de prueba entrenado con dibujos sintéticos. " +
          "Sirve para revisar que la demo funciona; reemplázalo por el que entrenen con sus datos (ver README).",
          "aviso-amarillo");
      }
      reconocer();
    })
    .catch((err) => {
      $("info-modelo").textContent = "Sin modelo";
      mostrarEstadoModelo(err.message === "sin-modelo"
        ? "Todavía no hay un modelo en static/modelo/. Entrénenlo con entrenamiento/entrenar.py y copien modelo.json y pesos.bin. Mientras tanto, solo se ve la segmentación."
        : "No se pudo cargar el modelo: " + err.message, "aviso-rojo");
    });

  function reconocer() {
    const grupos = segmentar(lienzo.trazos, C.grosor, MARGEN_SEGMENTACION);
    const rasters = grupos.map((g) => rasterizarGrupo(g, C.grosor));
    const entradas = rasters.map((r) => preprocesarAlfa(r.alfa, r.ancho, r.alto));
    const probs = modelo ? predecir(modelo, entradas) : [];

    simbolos = grupos.map((g, i) => {
      const s = { caja: g.caja, cabezaY: Pentagrama.cabezaY(rasters[i], SEP), clase: null, conf: 0 };
      if (modelo) {
        const orden = probs[i].map((p, k) => [p, k]).sort((a, b) => b[0] - a[0]);
        s.clase = C.clases[orden[0][1]];
        s.conf = orden[0][0];
        s.segunda = { clase: C.clases[orden[1][1]], conf: orden[1][0] };
        s.top = orden.slice(0, 4).map(([p, k]) => ({ clase: C.clases[k], conf: p }));
      }
      return s;
    });
    interpretar();
  }

  function umbral() { return Number($("umbral").value) / 100; }

  function interpretar() {
    eventos = Pentagrama.interpretar(simbolos, pentagrama, umbral());
    dibujarAnotaciones();
    llenarTabla();
    llenarProbabilidades();
    $("btn-play").disabled = eventos.length === 0;
    $("btn-midi").disabled = !eventos.some((e) => e.midi !== null);
  }

  function texto(t, x, y, color, negrita) {
    anot.font = (negrita ? "600 " : "") + "13px 'Instrument Sans', system-ui, sans-serif";
    anot.lineWidth = 4; anot.strokeStyle = "rgba(255,255,255,0.92)"; anot.lineJoin = "round";
    anot.strokeText(t, x, y);
    anot.fillStyle = color; anot.fillText(t, x, y);
  }

  function dibujarAnotaciones() {
    anot.clearRect(0, 0, ANCHO, ALTO);
    anot.textAlign = "center";
    const finDeFila = [-Infinity, -Infinity, -Infinity];
    simbolos.forEach((s, i) => {
      const x = s.caja.minX - 4, y = s.caja.minY - 4;
      const w = s.caja.maxX - s.caja.minX + 8, h = s.caja.maxY - s.caja.minY + 8;
      const cx = x + w / 2;
      const color = !modelo ? COLORES.suave : s.valido ? COLORES.azul : COLORES.alerta;

      if (i === sonando) { anot.fillStyle = COLORES.resalte; anot.fillRect(x - 4, 8, w + 8, ALTO - 16); }

      anot.save();
      anot.strokeStyle = color; anot.lineWidth = s.valido || !modelo ? 1.2 : 1.8;
      if (modelo && !s.valido) anot.setLineDash([5, 4]);
      anot.strokeRect(x, y, w, h);
      anot.restore();

      const etiqueta = !modelo ? "símbolo " + (i + 1)
        : s.valido ? `${s.clase.nombre} ${Math.round(100 * s.conf)}%`
        : `¿${s.clase.nombre}? ${Math.round(100 * s.conf)}% · redibuja`;
      anot.font = "600 13px 'Instrument Sans', system-ui, sans-serif";
      const ancho = anot.measureText(etiqueta).width;
      let fila = finDeFila.findIndex((fin) => cx - ancho / 2 > fin + 8);
      if (fila < 0) fila = finDeFila.indexOf(Math.min(...finDeFila));
      finDeFila[fila] = cx + ancho / 2;
      const yEtiqueta = 22 + fila * 17;
      anot.save(); anot.strokeStyle = color; anot.globalAlpha = 0.35; anot.lineWidth = 1;
      anot.beginPath(); anot.moveTo(cx, yEtiqueta + 4); anot.lineTo(cx, y); anot.stroke(); anot.restore();
      texto(etiqueta, cx, yEtiqueta, color, true);

      if (s.nota) {
        texto(s.nota.nombre, cx, Math.min(ALTO - 6, y + h + 17), COLORES.tinta, false);
        anot.strokeStyle = "#A9B8D6"; anot.lineWidth = 1.5;
        const lineas = [];
        for (let p = -2; p >= s.posicion; p -= 2) lineas.push(p);
        for (let p = 10; p <= s.posicion; p += 2) lineas.push(p);
        lineas.forEach((p) => {
          const ly = Math.round(pentagrama.yDePosicion(p)) + 0.5;
          anot.beginPath(); anot.moveTo(cx - 20, ly); anot.lineTo(cx + 20, ly); anot.stroke();
        });
      }
    });
  }

  function llenarTabla() {
    const cuerpo = $("cuerpo-tabla");
    cuerpo.innerHTML = "";
    if (!simbolos.length) {
      cuerpo.innerHTML = '<tr class="vacia"><td colspan="5">Aún no hay figuras. Empieza con una clave de sol a la izquierda.</td></tr>';
      return;
    }
    simbolos.forEach((s, i) => {
      const tr = document.createElement("tr");
      if (modelo && !s.valido) tr.className = "bajo";
      if (i === sonando) tr.className = "sonando";
      if (modelo && i === indiceSeleccionado()) tr.classList.add("elegido");
      if (modelo) tr.addEventListener("click", () => { seleccionado = i; llenarTabla(); llenarProbabilidades(); });
      const pct = Math.round(100 * s.conf);
      tr.innerHTML = !modelo
        ? `<td class="g">?</td><td>Símbolo ${i + 1}</td><td class="suave">Sin modelo</td><td></td><td></td>`
        : `<td class="g" aria-hidden="true">${s.clase.simbolo}</td>
           <td>${s.clase.nombre}</td>
           <td>${s.valido ? s.detalle : '<span class="etiqueta-bajo">Confianza baja: redibuja</span>'}</td>
           <td><span class="conf"><span class="barra"><span style="width:${pct}%;background:${s.valido ? "" : COLORES.alerta}"></span></span>${pct}%</span></td>
           <td class="suave">${s.segunda.clase.nombre} ${Math.round(100 * s.segunda.conf)}%</td>`;
      cuerpo.appendChild(tr);
    });
  }

  const TIPOS = { nota: "Figura", silencio: "Silencio", clave: "Clave", alteracion: "Alteración" };

  function indiceSeleccionado() {
    if (!simbolos.length) return null;
    return seleccionado !== null && seleccionado < simbolos.length ? seleccionado : simbolos.length - 1;
  }

  function llenarProbabilidades() {
    const panel = $("panel-probabilidades");
    const i = indiceSeleccionado();
    if (i === null) { panel.innerHTML = '<p class="suave">Aún no hay figuras.</p>'; return; }
    if (!modelo) { panel.innerHTML = '<p class="suave">Sin modelo: no hay probabilidades.</p>'; return; }
    const s = simbolos[i];
    const nombre = (c) => `${TIPOS[c.tipo] || c.tipo}: ${c.nombre.toLowerCase()}`;
    const pct = (p) => (100 * p).toFixed(2) + "%";
    panel.innerHTML =
      `<p class="prob-titulo"><span class="g" aria-hidden="true">${s.clase.simbolo}</span>${nombre(s.clase)} (${pct(s.conf)})</p>
       <p class="suave chico">Símbolo ${i + 1} de ${simbolos.length}${simbolos.length > 1 ? " · haz clic en una fila de la tabla para ver otro" : ""}</p>
       <ul class="lista-probabilidades">` +
      s.top.map((t) =>
        `<li><span class="g" aria-hidden="true">${t.clase.simbolo}</span>
             <span class="nombre">${nombre(t.clase)}</span>
             <span class="barra"><span style="width:${100 * t.conf}%"></span></span>
             <span class="cifra">${pct(t.conf)}</span></li>`).join("") +
      `</ul>`;
  }

  function alternarPlay() {
    if ($("btn-play").dataset.sonando === "1") { terminar(); return; }
    if (!eventos.length) return;
    $("btn-play").dataset.sonando = "1";
    $("btn-play").textContent = "Detener";
    reproductor.reproducir(eventos, Number($("bpm").value),
      (ev) => { sonando = ev ? ev.indice : null; dibujarAnotaciones(); llenarTabla(); },
      terminar);
  }

  function terminar() {
    reproductor.detener();
    sonando = null;
    $("btn-play").dataset.sonando = "0";
    $("btn-play").textContent = "Reproducir";
    dibujarAnotaciones(); llenarTabla();
  }

  function descargarMidi() {
    const datos = crearMidi(eventos, Number($("bpm").value));
    const url = URL.createObjectURL(new Blob([datos], { type: "audio/midi" }));
    const a = document.createElement("a");
    a.href = url; a.download = "melodia.mid"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  $("btn-play").addEventListener("click", alternarPlay);
  $("btn-deshacer").addEventListener("click", () => { terminar(); lienzo.deshacer(); });
  $("btn-borrar").addEventListener("click", () => { terminar(); seleccionado = null; lienzo.borrar(); });
  $("btn-midi").addEventListener("click", descargarMidi);
  $("bpm").addEventListener("input", (e) => { $("bpm-valor").textContent = e.target.value; });
  $("umbral").addEventListener("input", (e) => { $("umbral-valor").textContent = e.target.value; interpretar(); });
  document.addEventListener("keydown", (e) => {
    if ((e.key === "z" || e.key === "Z") && !e.target.matches("input")) { terminar(); lienzo.deshacer(); }
  });

  interpretar();
  window.demo = { lienzo, reconocer, estado: () => ({ simbolos, eventos }) };
})();
