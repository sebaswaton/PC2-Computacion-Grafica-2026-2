(function (global) {
  "use strict";

  async function cargarModelo(base) {
    const r = await fetch(base + "modelo.json", { cache: "no-store" });
    if (!r.ok) throw new Error("sin-modelo");
    const info = await r.json();
    const binario = await (await fetch(base + info.archivo_pesos, { cache: "no-store" })).arrayBuffer();

    const red = tf.sequential();
    info.capas.forEach((capa, i) => {
      const extra = i === 0 ? { inputShape: info.forma_entrada } : {};
      switch (capa.tipo) {
        case "conv2d":
          red.add(tf.layers.conv2d(Object.assign({
            filters: capa.filtros, kernelSize: capa.kernel, strides: capa.paso,
            padding: capa.padding, activation: capa.activacion,
          }, extra)));
          break;
        case "maxpool":
          red.add(tf.layers.maxPooling2d(Object.assign({
            poolSize: capa.tam, strides: capa.paso, padding: capa.padding }, extra)));
          break;
        case "flatten":
          red.add(tf.layers.flatten(extra));
          break;
        case "dense":
          red.add(tf.layers.dense(Object.assign({ units: capa.unidades, activation: capa.activacion }, extra)));
          break;
        case "dropout":
          break;
        default:
          throw new Error("Capa no soportada: " + capa.tipo);
      }
    });

    const pesos = info.pesos.map((p) =>
      tf.tensor(new Float32Array(binario, p.inicio * 4, p.cantidad), p.forma));
    red.setWeights(pesos);
    pesos.forEach((t) => t.dispose());
    return { red: red, info: info };
  }

  function predecir(modelo, entradas) {
    if (!entradas.length) return [];
    const tam = modelo.info.forma_entrada[0];
    return tf.tidy(() => {
      const plano = new Float32Array(entradas.length * tam * tam);
      entradas.forEach((e, i) => plano.set(e, i * tam * tam));
      const x = tf.tensor4d(plano, [entradas.length, tam, tam, 1]);
      return modelo.red.predict(x).arraySync();
    });
  }

  global.cargarModelo = cargarModelo;
  global.predecir = predecir;
})(window);
