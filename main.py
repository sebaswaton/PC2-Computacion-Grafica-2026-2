import base64
import io
import os
import random
import re
import tempfile
import uuid
import zipfile
from datetime import datetime

import numpy as np
from flask import Flask, abort, jsonify, render_template, request, send_file
from PIL import Image

import clases as cfg
from dataset import (PATRON_AUTOR, SEPARADOR, autor_de_archivo, construir_dataset,
                     conteos, crear_carpetas, rutas_de_clase)

DATA_DIR = (os.environ.get("DATA_DIR")
            or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
            or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
DATASET_DIR = os.path.join(DATA_DIR, "dataset")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

PATRON_ARCHIVO = re.compile(r"^[a-z0-9_]{2,30}__\d{8}-\d{6}_[0-9a-f]{8}\.png$")
MIN_PIXELES_TINTA = 30


def config_para_js():
    return {
        "clases": cfg.CLASES,
        "grosor": cfg.GROSOR_TRAZO,
        "separacion": cfg.SEPARACION_LINEAS,
        "lienzo": cfg.LIENZO_RECOLECCION,
        "tam": cfg.TAM_ENTRADA,
        "metaMin": cfg.META_MINIMA,
        "metaMax": cfg.META_MAXIMA,
    }


def autor_valido(autor):
    return isinstance(autor, str) and PATRON_AUTOR.match(autor) is not None


def elegir_siguiente(totales, del_autor):
    minimo_autor = min(del_autor)
    candidatas = [i for i, n in enumerate(del_autor) if n == minimo_autor]
    minimo_total = min(totales[i] for i in candidatas)
    candidatas = [i for i in candidatas if totales[i] == minimo_total]
    return random.choice(candidatas)


def estado(autor=None):
    totales, del_autor, por_autor = conteos(DATA_DIR, autor)
    return {
        "totales": totales,
        "delAutor": del_autor,
        "total": sum(totales),
        "totalAutor": sum(del_autor),
        "autores": len(por_autor),
        "siguiente": elegir_siguiente(totales, del_autor),
    }


@app.route("/")
def pagina_recolectar():
    return render_template("recolectar.html", config=config_para_js())


@app.route("/demo")
def pagina_demo():
    return render_template("demo.html", config=config_para_js())


@app.route("/datos")
def pagina_datos():
    totales, _, por_autor = conteos(DATA_DIR)
    filas = [{"nombre": c["nombre"], "simbolo": c["simbolo"], "total": t}
             for c, t in zip(cfg.CLASES, totales)]
    prueba = {a: n for a, n in por_autor.items() if a.startswith("test_")}
    return render_template("datos.html", config=config_para_js(), filas=filas,
                           total=sum(totales), por_autor=sorted(por_autor.items()),
                           prueba=prueba, data_dir=DATA_DIR,
                           dataset_listo=os.path.exists(os.path.join(DATASET_DIR, "X.npy")))


@app.route("/api/estado")
def api_estado():
    autor = request.args.get("autor", "")
    return jsonify(estado(autor if autor_valido(autor) else None))


@app.route("/api/muestra", methods=["POST"])
def api_muestra():
    datos = request.get_json(silent=True) or {}
    autor, clase, imagen = datos.get("autor"), datos.get("clase"), datos.get("imagen", "")

    if not autor_valido(autor):
        return jsonify(ok=False, error="Nombre de autor inválido (usa letras minúsculas, números y _)."), 400
    if clase not in cfg.CARPETAS:
        return jsonify(ok=False, error="Clase desconocida."), 400
    if not isinstance(imagen, str) or not imagen.startswith("data:image/png;base64,"):
        return jsonify(ok=False, error="Imagen inválida."), 400

    try:
        crudo = base64.b64decode(imagen.split(",", 1)[1], validate=True)
        with Image.open(io.BytesIO(crudo)) as im:
            im = im.convert("RGBA")
            if im.size != (cfg.LIENZO_RECOLECCION, cfg.LIENZO_RECOLECCION):
                return jsonify(ok=False, error="Tamaño de lienzo inesperado."), 400
            alfa = np.array(im)[:, :, 3]
    except Exception:
        return jsonify(ok=False, error="No se pudo leer la imagen."), 400

    if int((alfa > 10).sum()) < MIN_PIXELES_TINTA:
        return jsonify(ok=False, error="El dibujo está vacío."), 400

    crear_carpetas(DATA_DIR)
    nombre = f"{autor}{SEPARADOR}{datetime.now():%Y%m%d-%H%M%S}_{uuid.uuid4().hex[:8]}.png"
    with open(os.path.join(DATA_DIR, clase, nombre), "wb") as f:
        f.write(crudo)

    return jsonify(ok=True, archivo=nombre, clase=clase, estado=estado(autor))


@app.route("/api/borrar", methods=["POST"])
def api_borrar():
    datos = request.get_json(silent=True) or {}
    autor, clase, archivo = datos.get("autor"), datos.get("clase"), datos.get("archivo", "")
    if (not autor_valido(autor) or clase not in cfg.CARPETAS
            or not PATRON_ARCHIVO.match(archivo) or autor_de_archivo(archivo) != autor):
        return jsonify(ok=False, error="Petición inválida."), 400
    ruta = os.path.join(DATA_DIR, clase, archivo)
    if os.path.exists(ruta):
        os.remove(ruta)
    return jsonify(ok=True, estado=estado(autor))


@app.route("/prepare", methods=["GET", "POST"])
def preparar():
    resumen = construir_dataset(DATA_DIR, DATASET_DIR)
    return jsonify(ok=True, **resumen)


def _enviar_dataset(nombre):
    ruta = os.path.join(DATASET_DIR, nombre)
    if not os.path.exists(ruta):
        abort(404, description="Primero ejecuta /prepare.")
    return send_file(ruta, as_attachment=True, download_name=nombre)


@app.route("/X.npy")
def descargar_X():
    return _enviar_dataset("X.npy")


@app.route("/y.npy")
def descargar_y():
    return _enviar_dataset("y.npy")


@app.route("/autores.npy")
def descargar_autores():
    return _enviar_dataset("autores.npy")


@app.route("/clases.json")
def descargar_clases():
    return _enviar_dataset("clases.json")


@app.route("/descargar/datos.zip")
def descargar_zip():
    tmp = tempfile.SpooledTemporaryFile(max_size=50 * 1024 * 1024)
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as z:
        for carpeta in cfg.CARPETAS:
            for ruta in rutas_de_clase(DATA_DIR, carpeta):
                z.write(ruta, "data/" + os.path.relpath(ruta, DATA_DIR))
    tmp.seek(0)
    return send_file(tmp, mimetype="application/zip", as_attachment=True,
                     download_name=f"datos_{datetime.now():%Y%m%d-%H%M}.zip")


if __name__ == "__main__":
    print(f"Guardando datos en: {DATA_DIR}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
