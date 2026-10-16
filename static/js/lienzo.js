(function (global) {
  "use strict";

  function dibujarTrazos(ctx, trazos, grosor, color, dx, dy) {
    dx = dx || 0; dy = dy || 0;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = grosor;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    for (const t of trazos) {
      const p = t.puntos;
      if (p.length === 1) {
        ctx.beginPath();
        ctx.arc(p[0].x + dx, p[0].y + dy, grosor / 2, 0, Math.PI * 2);
        ctx.fill();
        continue;
      }
      ctx.beginPath();
      ctx.moveTo(p[0].x + dx, p[0].y + dy);
      for (let i = 1; i < p.length; i++) ctx.lineTo(p[i].x + dx, p[i].y + dy);
      ctx.stroke();
    }
    ctx.restore();
  }

  function cajaDeTrazo(t, grosor) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const p of t.puntos) {
      if (p.x < minX) minX = p.x; if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y; if (p.y > maxY) maxY = p.y;
    }
    const m = grosor / 2 + 1;
    return { minX: minX - m, minY: minY - m, maxX: maxX + m, maxY: maxY + m };
  }

  class LienzoTrazos {
    constructor(canvas, opciones) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.grosor = opciones.grosor;
      this.color = opciones.color || "#1A2238";
      this.alCambiar = opciones.alCambiar || function () {};
      this.trazos = [];
      this.actual = null;
      this.habilitado = true;

      canvas.addEventListener("pointerdown", (e) => this._inicio(e));
      canvas.addEventListener("pointermove", (e) => this._mover(e));
      canvas.addEventListener("pointerup", (e) => this._fin(e));
      canvas.addEventListener("pointercancel", (e) => this._fin(e));
    }

    _punto(e) {
      const r = this.canvas.getBoundingClientRect();
      return {
        x: (e.clientX - r.left) * (this.canvas.width / r.width),
        y: (e.clientY - r.top) * (this.canvas.height / r.height),
      };
    }

    _inicio(e) {
      if (!this.habilitado || (e.pointerType === "mouse" && e.button !== 0)) return;
      e.preventDefault();
      this.canvas.setPointerCapture(e.pointerId);
      this.actual = { puntos: [this._punto(e)] };
      this.trazos.push(this.actual);
      this.redibujar();
    }

    _mover(e) {
      if (!this.actual) return;
      e.preventDefault();
      const eventos = e.getCoalescedEvents ? e.getCoalescedEvents() : [e];
      for (const ev of (eventos.length ? eventos : [e])) this.actual.puntos.push(this._punto(ev));
      this.redibujar();
    }

    _fin() {
      if (!this.actual) return;
      this.actual = null;
      this.alCambiar(this.trazos);
    }

    redibujar() {
      this.ctx.setTransform(1, 0, 0, 1, 0, 0);
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      dibujarTrazos(this.ctx, this.trazos, this.grosor, this.color);
    }

    deshacer() {
      this.trazos.pop();
      this.redibujar();
      this.alCambiar(this.trazos);
    }

    borrar() {
      this.trazos = [];
      this.redibujar();
      this.alCambiar(this.trazos);
    }

    vacio() { return this.trazos.length === 0; }
  }

  function dibujarPentagrama(canvas, yCentro, separacion, color, xIni, xFin) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    for (let i = -2; i <= 2; i++) {
      const y = Math.round(yCentro + i * separacion) + 0.5;
      ctx.beginPath();
      ctx.moveTo(xIni == null ? 0 : xIni, y);
      ctx.lineTo(xFin == null ? canvas.width : xFin, y);
      ctx.stroke();
    }
  }

  global.LienzoTrazos = LienzoTrazos;
  global.dibujarTrazos = dibujarTrazos;
  global.cajaDeTrazo = cajaDeTrazo;
  global.dibujarPentagrama = dibujarPentagrama;
})(window);
