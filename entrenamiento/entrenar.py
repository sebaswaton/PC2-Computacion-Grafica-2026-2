import argparse
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import keras
import tensorflow as tf
from keras import layers
from sklearn.metrics import (accuracy_score, confusion_matrix,
                             precision_recall_fscore_support)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from clases import CARPETAS, NOMBRES, NUM_CLASES, TAM_ENTRADA
from dataset import dividir_por_autor, dividir_por_grupos

SUAVIZADO_ETIQUETAS = 0.1
ABREV = ["Red", "Bla", "Neg", "Cor", "SNe", "SBl", "CSo", "CFa", "Sos", "Bem"]


def cargar(carpeta):
    X = np.load(os.path.join(carpeta, "X.npy")).astype("float32") / 255.0
    y = np.load(os.path.join(carpeta, "y.npy")).astype("int64")
    ruta_aut = os.path.join(carpeta, "autores.npy")
    autores = np.load(ruta_aut) if os.path.exists(ruta_aut) else np.array(["desconocido"] * len(y))
    ruta_gru = os.path.join(carpeta, "grupos.npy")
    grupos = np.load(ruta_gru) if os.path.exists(ruta_gru) else None
    return X[..., None], y, autores, grupos


def crear_aumento():
    return keras.Sequential([
        layers.RandomRotation(0.025, fill_mode="constant"),
        layers.RandomZoom((-0.12, 0.12), fill_mode="constant"),
        layers.RandomTranslation(0.08, 0.08, fill_mode="constant"),
        layers.GaussianNoise(0.04),
    ], name="aumento")


def crear_mlp():
    return keras.Sequential([
        keras.Input((TAM_ENTRADA, TAM_ENTRADA, 1)),
        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(NUM_CLASES, activation="softmax"),
    ], name="mlp")


def crear_cnn():
    return keras.Sequential([
        keras.Input((TAM_ENTRADA, TAM_ENTRADA, 1)),
        layers.Conv2D(32, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(2),
        layers.Dropout(0.25),
        layers.Conv2D(64, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(2),
        layers.Dropout(0.25),
        layers.Conv2D(128, 3, padding="same", activation="relu"),
        layers.MaxPooling2D(2),
        layers.Dropout(0.3),
        layers.Flatten(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.4),
        layers.Dense(NUM_CLASES, activation="softmax"),
    ], name="cnn")


def entrenar(modelo, aumento, Xe, ye, Xv, yv, epocas, lote, semilla):
    modelo.compile(optimizer=keras.optimizers.Adam(1e-3),
                   loss=keras.losses.CategoricalCrossentropy(label_smoothing=SUAVIZADO_ETIQUETAS),
                   metrics=[keras.metrics.CategoricalAccuracy(name="accuracy")])
    ds = (tf.data.Dataset.from_tensor_slices((Xe, ye))
          .shuffle(len(ye), seed=semilla)
          .batch(lote)
          .map(lambda x, y: (tf.clip_by_value(aumento(x, training=True), 0.0, 1.0), tf.one_hot(y, NUM_CLASES)),
               num_parallel_calls=tf.data.AUTOTUNE)
          .prefetch(tf.data.AUTOTUNE))
    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-5),
    ]
    t0 = time.time()
    hist = modelo.fit(ds, validation_data=(Xv, keras.utils.to_categorical(yv, NUM_CLASES)), epochs=epocas, callbacks=callbacks, verbose=2,
                     shuffle=False)
    return hist.history, time.time() - t0


def evaluar(modelo, X, y):
    t0 = time.time()
    probs = modelo.predict(X, verbose=0, batch_size=256)
    ms = 1000 * (time.time() - t0) / max(1, len(y))
    pred = probs.argmax(1)
    p, r, f, s = precision_recall_fscore_support(y, pred, labels=range(NUM_CLASES), zero_division=0)
    pm, rm, fm, _ = precision_recall_fscore_support(y, pred, average="macro", zero_division=0)
    return {
        "exactitud": float(accuracy_score(y, pred)),
        "precision_macro": float(pm), "recall_macro": float(rm), "f1_macro": float(fm),
        "por_clase": [{"clase": NOMBRES[i], "precision": float(p[i]), "recall": float(r[i]),
                       "f1": float(f[i]), "soporte": int(s[i])} for i in range(NUM_CLASES)],
        "matriz": confusion_matrix(y, pred, labels=range(NUM_CLASES)).tolist(),
        "pred": pred, "probs": probs, "ms_por_imagen": ms,
    }


def pares_confundidos(matriz, n=6):
    m = np.array(matriz)
    pares = [(m[i, j], i, j) for i in range(NUM_CLASES) for j in range(NUM_CLASES) if i != j and m[i, j] > 0]
    return sorted(pares, reverse=True)[:n]


def graficar_curvas(historiales, ruta):
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4))
    colores = {"mlp": "#9AA3B8", "cnn": "#2D4F9E"}
    for nombre, h in historiales.items():
        c = colores[nombre]
        ejes[0].plot(h["loss"], color=c, ls="--", label=f"{nombre.upper()} entrenamiento")
        ejes[0].plot(h["val_loss"], color=c, label=f"{nombre.upper()} validación")
        ejes[1].plot(h["accuracy"], color=c, ls="--", label=f"{nombre.upper()} entrenamiento")
        ejes[1].plot(h["val_accuracy"], color=c, label=f"{nombre.upper()} validación")
    ejes[0].set_title("Pérdida (loss)"); ejes[1].set_title("Exactitud (accuracy)")
    for e in ejes:
        e.set_xlabel("Época"); e.grid(alpha=0.3); e.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(ruta, dpi=130); plt.close(fig)


def graficar_matriz(matriz, titulo, ruta):
    m = np.array(matriz, dtype=float)
    norm = m / np.maximum(m.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(NUM_CLASES), ABREV); ax.set_yticks(range(NUM_CLASES), NOMBRES)
    ax.set_xlabel("Predicción"); ax.set_ylabel("Clase real"); ax.set_title(titulo)
    for i in range(NUM_CLASES):
        for j in range(NUM_CLASES):
            if m[i, j]:
                ax.text(j, i, int(m[i, j]), ha="center", va="center", fontsize=8,
                        color="white" if norm[i, j] > 0.5 else "#1A2238")
    fig.tight_layout(); fig.savefig(ruta, dpi=130); plt.close(fig)


def graficar_errores(X, y, pred, probs, ruta, n=24):
    errores = np.where(pred != y)[0][:n]
    if len(errores) == 0:
        return False
    cols = 8
    filas = int(np.ceil(len(errores) / cols))
    fig, ejes = plt.subplots(filas, cols, figsize=(cols * 1.6, filas * 1.9))
    for k, ax in enumerate(np.array(ejes).reshape(-1)):
        ax.axis("off")
        if k < len(errores):
            i = errores[k]
            ax.imshow(1 - X[i, :, :, 0], cmap="gray", vmin=0, vmax=1)
            ax.set_title(f"real {ABREV[y[i]]}\npred {ABREV[pred[i]]} {probs[i].max():.0%}", fontsize=8)
    fig.tight_layout(); fig.savefig(ruta, dpi=120); plt.close(fig)
    return True


def exportar_web(modelo, carpeta, extra):
    os.makedirs(carpeta, exist_ok=True)
    capas = []
    for capa in modelo.layers:
        nombre = type(capa).__name__
        c = capa.get_config()
        if nombre == "Conv2D":
            capas.append({"tipo": "conv2d", "filtros": c["filters"], "kernel": list(c["kernel_size"]),
                          "paso": list(c["strides"]), "padding": c["padding"], "activacion": c["activation"]})
        elif nombre == "MaxPooling2D":
            capas.append({"tipo": "maxpool", "tam": list(c["pool_size"]), "paso": list(c["strides"]),
                          "padding": c["padding"]})
        elif nombre == "Flatten":
            capas.append({"tipo": "flatten"})
        elif nombre == "Dense":
            capas.append({"tipo": "dense", "unidades": c["units"], "activacion": c["activation"]})
        elif nombre == "Dropout":
            capas.append({"tipo": "dropout"})
        else:
            raise ValueError(f"Capa {nombre} no soportada por el exportador web")

    pesos, especificacion, inicio = [], [], 0
    for w in modelo.get_weights():
        w = np.asarray(w, dtype="<f4")
        especificacion.append({"forma": list(w.shape), "inicio": inicio, "cantidad": int(w.size)})
        pesos.append(w.ravel())
        inicio += w.size
    np.concatenate(pesos).tofile(os.path.join(carpeta, "pesos.bin"))

    info = dict(extra)
    info.update({"forma_entrada": [TAM_ENTRADA, TAM_ENTRADA, 1], "clases": CARPETAS,
                 "capas": capas, "pesos": especificacion, "archivo_pesos": "pesos.bin"})
    with open(os.path.join(carpeta, "modelo.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)


def tabla(encabezado, filas):
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "|".join(["---"] * len(encabezado)) + "|"]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def pct(x):
    return f"{100 * x:.1f} %"


def escribir_informe(ruta, r, conteos, config, mejor, origen):
    md = ["# Resultados del entrenamiento", "",
          f"Generado el {datetime.now():%Y-%m-%d %H:%M}. Datos: "
          f"**{'recolectados por el equipo' if origen == 'real' else 'sintéticos (solo prueba)'}**.", ""]
    if origen == "sintetico":
        md += ["> **Atención:** estas métricas son de dibujos SINTÉTICOS (prueba del flujo). "
               "No las presenten: vuelvan a ejecutar el script con sus datos reales.", ""]

    md += ["## 1. Datos", "", tabla(["Clase", "Entrenamiento", "Validación", "Prueba"],
           [[NOMBRES[i], conteos["ent"][i], conteos["val"][i], conteos["pru"][i]] for i in range(NUM_CLASES)]
           + [["**Total**", sum(conteos["ent"]), sum(conteos["val"]), sum(conteos["pru"])]]), ""]

    md += ["## 2. Comparación MLP vs CNN (conjunto de prueba)", "",
           tabla(["Modelo", "Parámetros", "Exactitud", "Precisión (macro)", "Recall (macro)", "F1 (macro)",
                  "Épocas", "Tiempo de entrenamiento", "Inferencia por imagen"],
                 [[n.upper(), f"{r[n]['parametros']:,}".replace(",", " "), pct(r[n]["exactitud"]),
                   pct(r[n]["precision_macro"]), pct(r[n]["recall_macro"]), pct(r[n]["f1_macro"]),
                   r[n]["epocas"], f"{r[n]['segundos']:.0f} s", f"{r[n]['ms_por_imagen']:.2f} ms"]
                  for n in ("mlp", "cnn")]), "",
           f"Modelo exportado a la demo: **{mejor.upper()}** (elegido por exactitud en validación: "
           f"MLP {pct(r['mlp']['val_exactitud'])}, CNN {pct(r['cnn']['val_exactitud'])}).", ""]

    for n in ("cnn", "mlp"):
        md += [f"## {'3' if n == 'cnn' else '4'}. Métricas por clase — {n.upper()}", "",
               tabla(["Clase", "Precisión", "Recall", "F1", "Soporte"],
                     [[c["clase"], pct(c["precision"]), pct(c["recall"]), pct(c["f1"]), c["soporte"]]
                      for c in r[n]["por_clase"]]), ""]

    m = r["cnn"]["matriz"]
    md += ["## 5. Matriz de confusión — CNN (filas = clase real, columnas = predicción)", "",
           tabla(["Real \\ Pred"] + ABREV, [[ABREV[i]] + m[i] for i in range(NUM_CLASES)]), "",
           "Abreviaturas: " + ", ".join(f"{a} = {n}" for a, n in zip(ABREV, NOMBRES)) + ".", "",
           "## 6. Pares más confundidos (CNN)", ""]
    pares = pares_confundidos(m)
    md += [tabla(["Clase real", "Predicha como", "Casos"], [[NOMBRES[i], NOMBRES[j], c] for c, i, j in pares])
           if pares else "No hubo confusiones en el conjunto de prueba.", ""]

    md += ["## 7. Configuración", "",
           tabla(["Parámetro", "Valor"], [[k, v] for k, v in config.items()]), "",
           "Figuras: `curvas.png`, `matriz_cnn.png`, `matriz_mlp.png`, `errores_cnn.png`.", ""]
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", default=os.path.join(RAIZ, "data_aumentada", "dataset"))
    ap.add_argument("--salida", default=os.path.join(RAIZ, "entrenamiento", "resultados"))
    ap.add_argument("--exportar", default=os.path.join(RAIZ, "static", "modelo"))
    ap.add_argument("--epocas", type=int, default=40)
    ap.add_argument("--lote", type=int, default=64)
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--prueba-auto", type=float, default=0.15)
    ap.add_argument("--autor-prueba", default=None,
                    help="deja a este integrante FUERA del entrenamiento y lo usa como prueba "
                         "(p. ej. sebastian). Sin esto, la división es 70/20/10 al azar.")
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--origen", choices=["real", "sintetico"], default="real")
    args = ap.parse_args()

    keras.utils.set_random_seed(args.semilla)
    os.makedirs(args.salida, exist_ok=True)

    X, y, autores, grupos = cargar(args.datos)
    print(f"Datos: {X.shape[0]} imágenes de {X.shape[1]}x{X.shape[2]}"
          + (f" ({len(np.unique(grupos))} dibujos originales)" if grupos is not None else ""))
    if args.autor_prueba:
        ie, iv, ip = dividir_por_autor(y, grupos, autores, args.autor_prueba,
                                       val=args.val / (1 - args.prueba_auto), semilla=args.semilla)
        print(f"Prueba = todos los dibujos de '{args.autor_prueba}' (no vistos en el entrenamiento)")
    else:
        ie, iv, ip = dividir_por_grupos(y, grupos, args.val, args.prueba_auto, args.semilla)
    conteos = {k: np.bincount(y[i], minlength=NUM_CLASES).tolist() for k, i in (("ent", ie), ("val", iv), ("pru", ip))}
    print("Entrenamiento / validación / prueba:", len(ie), len(iv), len(ip))

    aumento = crear_aumento()
    resultados, historiales, modelos = {}, {}, {}
    for nombre, fabrica in (("mlp", crear_mlp), ("cnn", crear_cnn)):
        print(f"\n===== Entrenando {nombre.upper()} =====")
        keras.utils.set_random_seed(args.semilla)
        modelo = fabrica()
        modelo.summary()
        hist, seg = entrenar(modelo, aumento, X[ie], y[ie], X[iv], y[iv], args.epocas, args.lote, args.semilla)
        ev = evaluar(modelo, X[ip], y[ip])
        ev_val = evaluar(modelo, X[iv], y[iv])
        ev.update({"parametros": modelo.count_params(), "segundos": seg, "epocas": len(hist["loss"]),
                   "val_exactitud": ev_val["exactitud"]})
        resultados[nombre], historiales[nombre], modelos[nombre] = ev, hist, modelo
        modelo.save(os.path.join(args.salida, f"modelo_{nombre}.keras"))
        print(f"{nombre.upper()}: exactitud prueba {ev['exactitud']:.4f} · F1 macro {ev['f1_macro']:.4f}")

    graficar_curvas(historiales, os.path.join(args.salida, "curvas.png"))
    for n in ("mlp", "cnn"):
        graficar_matriz(resultados[n]["matriz"], f"Matriz de confusión — {n.upper()} (prueba)",
                        os.path.join(args.salida, f"matriz_{n}.png"))
    graficar_errores(X[ip], y[ip], resultados["cnn"]["pred"], resultados["cnn"]["probs"],
                     os.path.join(args.salida, "errores_cnn.png"))

    mejor = max(("mlp", "cnn"), key=lambda n: resultados[n]["val_exactitud"])
    config = {
        "Entrada": f"{TAM_ENTRADA}x{TAM_ENTRADA}x1, valores 0–1",
        "Optimizador": "Adam, lr inicial 0.001 (ReduceLROnPlateau x0.5)",
        "Pérdida": f"categorical_crossentropy con label smoothing {SUAVIZADO_ETIQUETAS}",
        "Épocas máximas": f"{args.epocas} (EarlyStopping, paciencia 8)",
        "Tamaño de lote": args.lote,
        "Aumento": "rotación ±9°, zoom ±12 %, desplazamiento ±8 %, ruido gaussiano σ=0.04",
        "Entrenamiento": (f"dibujos de los demás integrantes (sin '{args.autor_prueba}'), ~82 % al azar"
                          if args.autor_prueba else
                          f"{round((1 - args.val - args.prueba_auto) * 100)} % al azar, estratificado por clase"),
        "Validación": (f"~18 % al azar de los demás integrantes" if args.autor_prueba else
                       f"{round(args.val * 100)} % al azar, estratificado por clase"),
        "Prueba": (f"TODO lo de '{args.autor_prueba}' (integrante no visto)" if args.autor_prueba else
                   f"{round(args.prueba_auto * 100)} % al azar, estratificado por clase"),
        "Unidad de división": "dibujo original (sus variantes aumentadas van juntas)" if grupos is not None else "imagen",
        "Semilla": args.semilla,
        "TensorFlow / Keras": f"{tf.__version__} / {keras.__version__}",
    }
    escribir_informe(os.path.join(args.salida, "metricas.md"), resultados, conteos, config, mejor, args.origen)

    limpio = {n: {k: v for k, v in r.items() if k not in ("pred", "probs")} for n, r in resultados.items()}
    with open(os.path.join(args.salida, "metricas.json"), "w", encoding="utf-8") as f:
        json.dump({"resultados": limpio, "historial": historiales, "conteos": conteos,
                   "mejor": mejor}, f, ensure_ascii=False, indent=1, default=float)

    exportar_web(modelos[mejor], args.exportar, {
        "arquitectura": mejor, "origen": args.origen, "fecha": f"{datetime.now():%Y-%m-%d}",
        "exactitud_prueba": round(resultados[mejor]["exactitud"], 4),
        "f1_macro_prueba": round(resultados[mejor]["f1_macro"], 4),
    })
    print(f"\nListo. Informe: {os.path.join(args.salida, 'metricas.md')}")
    print(f"Modelo para la demo ({mejor.upper()}): {args.exportar}")


if __name__ == "__main__":
    main()
