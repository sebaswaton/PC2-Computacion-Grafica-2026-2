import json
import os
import re
from collections import Counter

import numpy as np

from clases import CARPETAS, CLASES
from preprocesamiento import preprocesar_png

PATRON_AUTOR = re.compile(r"^[a-z0-9_]{2,30}$")
SEPARADOR = "__"
SUBCONJUNTOS = ("entrenamiento", "validacion", "prueba")


def autor_de_archivo(nombre_archivo: str) -> str:
    return nombre_archivo.split(SEPARADOR, 1)[0] if SEPARADOR in nombre_archivo else "desconocido"


def crear_carpetas(data_dir: str) -> None:
    for carpeta in CARPETAS:
        os.makedirs(os.path.join(data_dir, carpeta), exist_ok=True)


def listar_pngs(data_dir: str, carpeta: str):
    ruta = os.path.join(data_dir, carpeta)
    if not os.path.isdir(ruta):
        return []
    return sorted(f for f in os.listdir(ruta) if f.endswith(".png"))


def rutas_de_clase(data_dir: str, carpeta: str):
    rutas = []
    for base in [os.path.join(data_dir, sub) for sub in SUBCONJUNTOS] + [data_dir]:
        ruta = os.path.join(base, carpeta)
        if os.path.isdir(ruta):
            rutas += [os.path.join(ruta, f) for f in sorted(os.listdir(ruta)) if f.endswith(".png")]
    return rutas


def conteos(data_dir: str, autor: str | None = None):
    totales, del_autor = [], []
    por_autor = Counter()
    for carpeta in CARPETAS:
        archivos = rutas_de_clase(data_dir, carpeta)
        totales.append(len(archivos))
        autores = [autor_de_archivo(os.path.basename(f)) for f in archivos]
        por_autor.update(autores)
        del_autor.append(sum(1 for a in autores if a == autor) if autor else 0)
    return totales, del_autor, por_autor


def dividir_por_grupos(y, grupos, val=0.20, prueba=0.10, semilla=42):
    y = np.asarray(y)
    grupos = np.arange(len(y)) if grupos is None else np.asarray(grupos)
    rng = np.random.default_rng(semilla)
    sets = {"ent": [], "val": [], "pru": []}
    for c in np.unique(y):
        gs = rng.permutation(np.unique(grupos[y == c]))
        n_pru = max(1, round(len(gs) * prueba)) if prueba > 0 else 0
        n_val = max(1, round(len(gs) * val))
        corte = {"pru": gs[:n_pru], "val": gs[n_pru:n_pru + n_val], "ent": gs[n_pru + n_val:]}
        for k, g in corte.items():
            sets[k].append(np.where((y == c) & np.isin(grupos, g))[0])
    return tuple(np.sort(np.concatenate(sets[k])) for k in ("ent", "val", "pru"))


def dividir_por_autor(y, grupos, autores, autor_prueba, val=0.20, semilla=42):
    autores = np.asarray(autores)
    if autor_prueba not in set(autores.tolist()):
        raise ValueError(f"autor '{autor_prueba}' no está en los datos: {sorted(set(autores.tolist()))}")
    ip = np.where(autores == autor_prueba)[0]
    resto = np.where(autores != autor_prueba)[0]
    grupos_resto = None if grupos is None else np.asarray(grupos)[resto]
    ie_r, iv_r, _ = dividir_por_grupos(y[resto], grupos_resto, val=val, prueba=0.0, semilla=semilla)
    return resto[ie_r], resto[iv_r], ip


def construir_dataset(data_dir: str, destino: str | None = None):
    destino = destino or os.path.join(data_dir, "dataset")
    os.makedirs(destino, exist_ok=True)

    X, y, autores = [], [], []
    for indice, carpeta in enumerate(CARPETAS):
        for ruta in rutas_de_clase(data_dir, carpeta):
            archivo = os.path.basename(ruta)
            try:
                img = preprocesar_png(ruta)
            except Exception as err:
                print(f"[aviso] no se pudo leer {ruta}: {err}")
                continue
            X.append(np.round(img * 255).astype(np.uint8))
            y.append(indice)
            autores.append(autor_de_archivo(archivo))

    X = np.stack(X) if X else np.zeros((0, 32, 32), dtype=np.uint8)
    y = np.array(y, dtype=np.int64)
    autores = np.array(autores, dtype=str)

    np.save(os.path.join(destino, "X.npy"), X)
    np.save(os.path.join(destino, "y.npy"), y)
    np.save(os.path.join(destino, "autores.npy"), autores)
    with open(os.path.join(destino, "clases.json"), "w", encoding="utf-8") as f:
        json.dump(CLASES, f, ensure_ascii=False, indent=2)

    resumen = {
        "total": int(len(y)),
        "por_clase": {c: int((y == i).sum()) for i, c in enumerate(CARPETAS)},
        "autores": dict(Counter(autores.tolist())),
        "forma_X": list(X.shape),
        "destino": destino,
    }
    return resumen


if __name__ == "__main__":
    import sys
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "data"
    print(json.dumps(construir_dataset(carpeta), ensure_ascii=False, indent=2))
