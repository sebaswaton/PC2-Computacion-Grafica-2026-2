import numpy as np
from PIL import Image

TAM = 32
UMBRAL_TINTA = 10
MARGEN_PCT = 12


def preprocesar_alfa(alfa: np.ndarray) -> np.ndarray:
    alfa = np.asarray(alfa, dtype=np.float64)
    filas, cols = np.where(alfa > UMBRAL_TINTA)
    if filas.size == 0:
        return np.zeros((TAM, TAM), dtype=np.float32)

    y0, y1 = filas.min(), filas.max() + 1
    x0, x1 = cols.min(), cols.max() + 1
    alto, ancho = y1 - y0, x1 - x0

    lado = max(alto, ancho)
    lado_con_margen = lado + 2 * max(2, (lado * MARGEN_PCT) // 100)
    k = max(1, -(-lado_con_margen // TAM))
    lado_final = TAM * k

    cuadrado = np.zeros((lado_final, lado_final), dtype=np.float64)
    oy = (lado_final - alto) // 2
    ox = (lado_final - ancho) // 2
    cuadrado[oy:oy + alto, ox:ox + ancho] = alfa[y0:y1, x0:x1]

    reducida = cuadrado.reshape(TAM, k, TAM, k).mean(axis=(1, 3))
    return (reducida / 255.0).astype(np.float32)


def leer_alfa_png(ruta) -> np.ndarray:
    with Image.open(ruta) as im:
        return np.array(im.convert("RGBA"))[:, :, 3]


def preprocesar_png(ruta) -> np.ndarray:
    return preprocesar_alfa(leer_alfa_png(ruta))
