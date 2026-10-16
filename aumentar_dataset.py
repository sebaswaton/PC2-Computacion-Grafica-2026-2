import argparse
import json
import os
import random
from collections import Counter

import numpy as np
from PIL import Image, ImageFilter

from clases import CARPETAS, CLASES
from dataset import SEPARADOR, autor_de_archivo, listar_pngs
from preprocesamiento import leer_alfa_png, preprocesar_alfa

AUTORES = ("darcy", "giordano", "sebastian")
POR_CLASE = 60
IMAGENES_POR_CLASE = 425
IMAGENES_PRUEBA_POR_CLASE = 75
CARPETA_TEST = "test_test"
LADO_PNG = 240


def seleccionar(data_dir, rng, por_clase=POR_CLASE):
    base, resto = divmod(por_clase, len(AUTORES))
    elegidos = []
    for k, carpeta in enumerate(CARPETAS):
        archivos = listar_pngs(data_dir, carpeta)
        for i, autor in enumerate(AUTORES):
            n = base + (1 if (i - k) % len(AUTORES) < resto else 0)
            propios = [f for f in archivos if autor_de_archivo(f) == autor]
            if len(propios) < n:
                raise SystemExit(f"{autor} solo tiene {len(propios)} en {carpeta}; se necesitan {n}")
            elegidos += [(carpeta, f) for f in sorted(rng.sample(propios, n))]
    return elegidos


def seleccionar_prueba(data_dir):
    return [(c, f) for c in CARPETAS for f in listar_pngs(data_dir, c) if autor_de_archivo(f) == CARPETA_TEST]


def imagenes_por_original(elegidos, imagenes_por_clase, rng):
    cuantas = [0] * len(elegidos)
    for carpeta in CARPETAS:
        idx = [i for i, (c, _) in enumerate(elegidos) if c == carpeta]
        base, extra = divmod(imagenes_por_clase, len(idx))
        for i in idx:
            cuantas[i] = base
        for i in rng.sample(idx, extra):
            cuantas[i] += 1
    return cuantas


def recortar_en_lienzo(alfa):
    filas, cols = np.where(alfa > 10)
    if filas.size == 0:
        return Image.fromarray(alfa.astype(np.uint8))
    trazo = alfa[filas.min():filas.max() + 1, cols.min():cols.max() + 1]
    lado = int(max(trazo.shape) * 1.8) + 8
    lienzo = np.zeros((lado, lado), dtype=np.uint8)
    oy, ox = (lado - trazo.shape[0]) // 2, (lado - trazo.shape[1]) // 2
    lienzo[oy:oy + trazo.shape[0], ox:ox + trazo.shape[1]] = trazo
    return Image.fromarray(lienzo)


def variante(lienzo, rng):
    w, h = lienzo.size
    ang = np.deg2rad(rng.uniform(-10, 10))
    sx, sy = rng.uniform(0.85, 1.15), rng.uniform(0.85, 1.15)
    cizalla = rng.uniform(-0.15, 0.15)
    c, s = np.cos(ang), np.sin(ang)
    A = np.array([[c, -s], [s, c]]) @ np.array([[1, cizalla], [0, 1]]) @ np.diag([sx, sy])
    inv = np.linalg.inv(A)
    centro = np.array([w / 2, h / 2])
    desp = centro - inv @ centro + np.array([rng.uniform(-0.04, 0.04) * w, rng.uniform(-0.04, 0.04) * h])
    img = lienzo.transform((w, h), Image.AFFINE, (*inv[0], desp[0], *inv[1], desp[1]),
                           resample=Image.BILINEAR)
    grosor = rng.choice(["mas", "menos", "igual", "igual"])
    if grosor == "mas":
        img = img.filter(ImageFilter.MaxFilter(3))
    elif grosor == "menos":
        img = img.filter(ImageFilter.MinFilter(3))
    if rng.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 0.9)))
    return img


def a_png_240(alfa_img):
    filas, cols = np.where(np.asarray(alfa_img) > 10)
    if filas.size:
        alfa_img = alfa_img.crop((cols.min(), filas.min(), cols.max() + 1, filas.max() + 1))
    lado = max(alfa_img.size)
    lado_c = int(lado * 1.3)
    lienzo = Image.new("L", (lado_c, lado_c), 0)
    lienzo.paste(alfa_img, ((lado_c - alfa_img.width) // 2, (lado_c - alfa_img.height) // 2))
    alfa = lienzo.resize((LADO_PNG, LADO_PNG), Image.LANCZOS)
    rgba = Image.new("RGBA", (LADO_PNG, LADO_PNG), (0, 0, 0, 0))
    rgba.putalpha(alfa)
    return rgba


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", default="originales")
    ap.add_argument("--salida", default="data_aumentada_5000")
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--por-clase", type=int, default=POR_CLASE)
    ap.add_argument("--imagenes-por-clase", type=int, default=IMAGENES_POR_CLASE)
    ap.add_argument("--imagenes-prueba-por-clase", type=int, default=IMAGENES_PRUEBA_POR_CLASE)
    args = ap.parse_args()

    rng_py = random.Random(args.semilla)
    rng = np.random.default_rng(args.semilla)
    entrenamiento = seleccionar(args.datos, rng_py, args.por_clase)
    prueba = seleccionar_prueba(args.datos)
    elegidos = entrenamiento + prueba
    cuantas = (imagenes_por_original(entrenamiento, args.imagenes_por_clase, rng_py)
               + imagenes_por_original(prueba, args.imagenes_prueba_por_clase, rng_py))

    destino_npy = os.path.join(args.salida, "dataset")
    os.makedirs(destino_npy, exist_ok=True)
    for c in CARPETAS:
        os.makedirs(os.path.join(args.salida, c), exist_ok=True)

    X, y, autores, grupos = [], [], [], []
    for grupo, (carpeta, archivo) in enumerate(elegidos):
        alfa = leer_alfa_png(os.path.join(args.datos, carpeta, archivo))
        base = recortar_en_lienzo(alfa)
        nombre = archivo[:-4]
        for v in range(cuantas[grupo]):
            ruta = os.path.join(args.salida, carpeta, f"{nombre}{SEPARADOR}aug{v:02d}.png")
            if v == 0:
                png = Image.new("RGBA", alfa.shape[::-1], (0, 0, 0, 0))
                png.putalpha(Image.fromarray(alfa))
                alfa_v = alfa
            else:
                png = a_png_240(variante(base, rng))
                alfa_v = np.array(png)[:, :, 3]
            png.save(ruta)
            X.append(np.round(preprocesar_alfa(alfa_v) * 255).astype(np.uint8))
            y.append(CARPETAS.index(carpeta))
            autores.append(autor_de_archivo(archivo))
            grupos.append(grupo)

    X, y = np.stack(X), np.array(y, dtype=np.int64)
    np.save(os.path.join(destino_npy, "X.npy"), X)
    np.save(os.path.join(destino_npy, "y.npy"), y)
    np.save(os.path.join(destino_npy, "autores.npy"), np.array(autores, dtype=str))
    np.save(os.path.join(destino_npy, "grupos.npy"), np.array(grupos, dtype=np.int64))
    with open(os.path.join(destino_npy, "clases.json"), "w", encoding="utf-8") as f:
        json.dump(CLASES, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.salida, "seleccion.json"), "w", encoding="utf-8") as f:
        json.dump([{"grupo": i, "carpeta": c, "archivo": a} for i, (c, a) in enumerate(elegidos)],
                  f, ensure_ascii=False, indent=1)

    print(f"Originales: {len(elegidos)} | Imágenes totales: {len(y)} | X: {X.shape}")
    print("Por clase:", {c: int((y == i).sum()) for i, c in enumerate(CARPETAS)})
    print("Por integrante (originales):", dict(Counter(autor_de_archivo(a) for _, a in elegidos)))
    print("Guardado en:", os.path.abspath(args.salida))


if __name__ == "__main__":
    main()
