(function () {
  "use strict";
  const C = window.CONFIG;
  const $ = (id) => document.getElementById(id);

  const lienzo = new LienzoTrazos($("dibujo"), {
    grosor: C.grosor,
    alCambiar: actualizarBotones,
  });

  dibujarPentagrama($("pauta"), C.lienzo / 2, C.separacion, "#DCE3F0");

  let claseActual = null;
  let ultimoEnvio = null;
  let enviando = false;

  function leerGuardado(clave) { try { return localStorage.getItem(clave) || ""; } catch (e) { return ""; } }
  function guardar(clave, valor) { try { localStorage.setItem(clave, valor); } catch (e) { } }

  function crearSesion() {
    const bytes = new Uint8Array(5);
    crypto.getRandomValues(bytes);
    return "ses_" + Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  }

  let sesion = leerGuardado("sesionRecoleccion");
  if (!/^ses_[0-9a-f]{10}$/.test(sesion)) {
    sesion = crearSesion();
    guardar("sesionRecoleccion", sesion);
  }

  async function cargarEstado() {
    try {
      const r = await fetch("/api/estado?autor=" + encodeURIComponent(sesion));
      mostrarEstado(await r.json());
    } catch (e) {
      avisar("No hay conexión con el servidor. Revisa que esté encendido.", true);
    }
  }

  function mostrarEstado(est) {
    claseActual = est.siguiente;
    const clase = C.clases[claseActual];
    $("titulo-encargo").textContent = clase.nombre;
    $("glifo").textContent = clase.simbolo;
    $("consejo").textContent = clase.consejo;

    const lista = $("lista-clases");
    lista.innerHTML = "";
    C.clases.forEach((c, i) => {
      const total = est.totales[i];
      const pct = Math.min(100, (100 * total) / C.metaMin);
      const li = document.createElement("li");
      if (i === claseActual) li.className = "actual";
      li.innerHTML =
        `<span class="g" aria-hidden="true">${c.simbolo}</span>` +
        `<span class="nombre">${c.nombre}</span>` +
        `<span class="cifra">${total}</span>` +
        `<span class="barra"><span class="${total >= C.metaMin ? "completa" : ""}" style="width:${pct}%"></span></span>`;
      lista.appendChild(li);
    });
  }

  function avisar(texto, error) {
    const a = $("aviso");
    a.textContent = texto;
    a.className = "aviso " + (error ? "error" : "ok");
  }

  function actualizarBotones() {
    $("btn-enviar").disabled = enviando || lienzo.vacio() || claseActual === null;
    $("btn-deshacer").disabled = lienzo.vacio();
    $("btn-borrar").disabled = lienzo.vacio();
    $("btn-anular").disabled = !ultimoEnvio;
  }

  async function enviar() {
    if ($("btn-enviar").disabled) return;
    enviando = true; actualizarBotones();
    const clase = C.clases[claseActual];
    try {
      const r = await fetch("/api/muestra", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          autor: sesion,
          clase: clase.carpeta,
          imagen: $("dibujo").toDataURL("image/png"),
        }),
      });
      const datos = await r.json();
      if (!datos.ok) throw new Error(datos.error || "Error al guardar.");
      ultimoEnvio = { clase: datos.clase, archivo: datos.archivo, nombre: clase.nombre };
      avisar(`Guardado: ${clase.nombre}. Ahora la siguiente.`);
      lienzo.borrar();
      mostrarEstado(datos.estado);
    } catch (e) {
      avisar(e.message === "Failed to fetch" ? "No se pudo guardar: el servidor no responde." : e.message, true);
    } finally {
      enviando = false; actualizarBotones();
    }
  }

  async function anularUltimo() {
    if (!ultimoEnvio) return;
    try {
      const r = await fetch("/api/borrar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ autor: sesion, clase: ultimoEnvio.clase, archivo: ultimoEnvio.archivo }),
      });
      const datos = await r.json();
      if (!datos.ok) throw new Error(datos.error);
      avisar(`Eliminado tu último dibujo de ${ultimoEnvio.nombre}.`);
      ultimoEnvio = null;
      mostrarEstado(datos.estado);
    } catch (e) {
      avisar("No se pudo eliminar: " + e.message, true);
    }
    actualizarBotones();
  }

  $("btn-enviar").addEventListener("click", enviar);
  $("btn-deshacer").addEventListener("click", () => lienzo.deshacer());
  $("btn-borrar").addEventListener("click", () => lienzo.borrar());
  $("btn-anular").addEventListener("click", anularUltimo);
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT") return;
    if (e.key === "Enter") { e.preventDefault(); enviar(); }
    if (e.key === "z" || e.key === "Z") lienzo.deshacer();
  });

  actualizarBotones();
  cargarEstado();
})();
