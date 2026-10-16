(function (global) {
  "use strict";

  const frecuencia = (midi) => 440 * Math.pow(2, (midi - 69) / 12);

  class Reproductor {
    constructor() { this.ctx = null; this.nodos = []; this.relojes = []; }

    reproducir(eventos, bpm, alSonar, alTerminar) {
      this.detener();
      if (!this.ctx) this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      const ctx = this.ctx;
      ctx.resume();
      const seg = 60 / bpm;
      let t = ctx.currentTime + 0.12;
      for (const ev of eventos) {
        const dur = ev.tiempos * seg;
        if (ev.midi !== null) this._nota(ev.midi, t, dur);
        const espera = (t - ctx.currentTime) * 1000;
        this.relojes.push(setTimeout(() => alSonar(ev), espera));
        t += dur;
      }
      this.relojes.push(setTimeout(() => { alSonar(null); alTerminar(); },
                                   (t - ctx.currentTime) * 1000));
    }

    _nota(midi, t, dur) {
      const ctx = this.ctx;
      const fin = t + Math.max(0.08, dur * 0.92);
      const salida = ctx.createGain();
      salida.gain.setValueAtTime(0.0001, t);
      salida.gain.exponentialRampToValueAtTime(0.32, t + 0.015);
      salida.gain.exponentialRampToValueAtTime(0.12, t + Math.min(0.5, dur * 0.6));
      salida.gain.exponentialRampToValueAtTime(0.0001, fin);
      salida.connect(ctx.destination);
      [["triangle", 1, 1], ["sine", 2, 0.25]].forEach(([forma, mult, vol]) => {
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = forma;
        osc.frequency.value = frecuencia(midi) * mult;
        g.gain.value = vol;
        osc.connect(g).connect(salida);
        osc.start(t); osc.stop(fin + 0.02);
        this.nodos.push(osc);
      });
    }

    detener() {
      this.relojes.forEach(clearTimeout);
      this.relojes = [];
      this.nodos.forEach((n) => { try { n.stop(); } catch (e) { } });
      this.nodos = [];
    }
  }

  function vlq(n) {
    const bytes = [n & 0x7f];
    while ((n >>= 7)) bytes.unshift((n & 0x7f) | 0x80);
    return bytes;
  }

  function crearMidi(eventos, bpm) {
    const PPQ = 480;
    const pista = [];
    const microsPorNegra = Math.round(60000000 / bpm);
    pista.push(0x00, 0xff, 0x51, 0x03,
      (microsPorNegra >> 16) & 0xff, (microsPorNegra >> 8) & 0xff, microsPorNegra & 0xff);
    pista.push(0x00, 0xc0, 0x00);
    let espera = 0;
    for (const ev of eventos) {
      const ticks = Math.round(ev.tiempos * PPQ);
      if (ev.midi === null) { espera += ticks; continue; }
      pista.push(...vlq(espera), 0x90, ev.midi, 90);
      pista.push(...vlq(ticks), 0x80, ev.midi, 0);
      espera = 0;
    }
    pista.push(...vlq(espera), 0xff, 0x2f, 0x00);

    const u32 = (n) => [(n >>> 24) & 0xff, (n >>> 16) & 0xff, (n >>> 8) & 0xff, n & 0xff];
    const archivo = [
      0x4d, 0x54, 0x68, 0x64, ...u32(6), 0x00, 0x00, 0x00, 0x01, (PPQ >> 8) & 0xff, PPQ & 0xff,
      0x4d, 0x54, 0x72, 0x6b, ...u32(pista.length), ...pista,
    ];
    return new Uint8Array(archivo);
  }

  global.Reproductor = Reproductor;
  global.crearMidi = crearMidi;
})(window);
