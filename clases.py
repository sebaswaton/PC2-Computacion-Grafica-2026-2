CLASES = [
    {"carpeta": "redonda",         "nombre": "Redonda",           "simbolo": "\U0001D15D", "duracion": 4.0, "tipo": "nota",
     "consejo": "Óvalo hueco, sin plica."},
    {"carpeta": "blanca",          "nombre": "Blanca",            "simbolo": "\U0001D15E", "duracion": 2.0, "tipo": "nota",
     "consejo": "Óvalo hueco con plica. Alterna plica arriba y abajo."},
    {"carpeta": "negra",           "nombre": "Negra",             "simbolo": "♩",     "duracion": 1.0, "tipo": "nota",
     "consejo": "Óvalo relleno con plica. Alterna plica arriba y abajo."},
    {"carpeta": "corchea",         "nombre": "Corchea",           "simbolo": "♪",     "duracion": 0.5, "tipo": "nota",
     "consejo": "Negra con un corchete (bandera) en la punta de la plica."},
    {"carpeta": "silencio_negra",  "nombre": "Silencio de negra", "simbolo": "\U0001D13D", "duracion": 1.0, "tipo": "silencio",
     "consejo": "Zigzag vertical que termina en un gancho."},
    {"carpeta": "silencio_blanca", "nombre": "Silencio de blanca","simbolo": "\U0001D13C", "duracion": 2.0, "tipo": "silencio",
     "consejo": "Rectángulo pequeño relleno, apoyado sobre la línea del medio."},
    {"carpeta": "clave_sol",       "nombre": "Clave de sol",      "simbolo": "\U0001D11E", "duracion": 0.0, "tipo": "clave",
     "consejo": "La espiral rodea la 2.ª línea (sol). Ocupa todo el pentagrama."},
    {"carpeta": "clave_fa",        "nombre": "Clave de fa",       "simbolo": "\U0001D122", "duracion": 0.0, "tipo": "clave",
     "consejo": "Curva que nace en la 4.ª línea y dos puntos a su derecha (pegados a la curva)."},
    {"carpeta": "sostenido",       "nombre": "Sostenido",         "simbolo": "♯",     "duracion": 0.0, "tipo": "alteracion",
     "consejo": "Dos verticales y dos diagonales cortas (#)."},
    {"carpeta": "bemol",           "nombre": "Bemol",             "simbolo": "♭",     "duracion": 0.0, "tipo": "alteracion",
     "consejo": "Vertical larga con una pancita abajo a la derecha (b)."},
]

CARPETAS = [c["carpeta"] for c in CLASES]
NOMBRES = [c["nombre"] for c in CLASES]
NUM_CLASES = len(CLASES)

META_MINIMA = 500
META_MAXIMA = 500

GROSOR_TRAZO = 5
SEPARACION_LINEAS = 24
LIENZO_RECOLECCION = 240
TAM_ENTRADA = 32
