import argparse
import json
import os
import shutil

import numpy as np

from clases import CARPETAS, CLASES
from dataset import SEPARADOR, SUBCONJUNTOS, dividir_por_autor


def nombres_png(origen):
    with open(os.path.join(origen, "seleccion.json"), encoding="utf-8") as f:
        seleccion = json.load(f)
    grupos = np.load(os.path.join(origen, "dataset", "grupos.npy"))
    filas, visto = [], {}
    for g in grupos:
        v = visto.get(int(g), 0)
        visto[int(g)] = v + 1
        s = seleccion[int(g)]
        filas.append((s["carpeta"], f"{s['archivo'][:-4]}{SEPARADOR}aug{v:02d}.png"))
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origen", default="data_aumentada_5000")
    ap.add_argument("--destino", default="data")
    ap.add_argument("--autor-prueba", default="test_test")
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--prueba", type=float, default=0.15)
    ap.add_argument("--semilla", type=int, default=42)
    args = ap.parse_args()

    d = os.path.join(args.origen, "dataset")
    X, y = np.load(f"{d}/X.npy"), np.load(f"{d}/y.npy")
    autores, grupos = np.load(f"{d}/autores.npy"), np.load(f"{d}/grupos.npy")
    ie, iv, ip = dividir_por_autor(y, grupos, autores, args.autor_prueba,
                                   val=args.val / (1 - args.prueba), semilla=args.semilla)
    nombres = nombres_png(args.origen)

    for sub, idx in zip(SUBCONJUNTOS, (ie, iv, ip)):
        raiz = os.path.join(args.destino, sub)
        for c in CARPETAS:
            os.makedirs(os.path.join(raiz, c), exist_ok=True)
        for i in idx:
            carpeta, archivo = nombres[i]
            shutil.copy2(os.path.join(args.origen, carpeta, archivo), os.path.join(raiz, carpeta, archivo))
        np.save(os.path.join(raiz, "X.npy"), X[idx])
        np.save(os.path.join(raiz, "y.npy"), y[idx])
        np.save(os.path.join(raiz, "autores.npy"), autores[idx])
        np.save(os.path.join(raiz, "grupos.npy"), grupos[idx])
        print(f"{sub:14s} {len(idx):5d} imágenes ({100 * len(idx) / len(y):.1f} %)")
    with open(os.path.join(args.destino, "clases.json"), "w", encoding="utf-8") as f:
        json.dump(CLASES, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
