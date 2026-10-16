# Resultados del entrenamiento

Generado el 2026-10-16 05:16.

## 1. Datos

| Clase | Entrenamiento | Validación | Prueba |
|---|---|---|---|
| Redonda | 346 | 79 | 75 |
| Blanca | 346 | 79 | 75 |
| Negra | 346 | 79 | 75 |
| Corchea | 348 | 77 | 75 |
| Silencio de negra | 348 | 77 | 75 |
| Silencio de blanca | 347 | 78 | 75 |
| Clave de sol | 348 | 77 | 75 |
| Clave de fa | 347 | 78 | 75 |
| Sostenido | 347 | 78 | 75 |
| Bemol | 347 | 78 | 75 |
| **Total** | 3470 | 780 | 750 |

## 2. Comparación MLP vs CNN (conjunto de prueba)

| Modelo | Parámetros | Exactitud | Precisión (macro) | Recall (macro) | F1 (macro) | Épocas | Tiempo de entrenamiento | Inferencia por imagen |
|---|---|---|---|---|---|---|---|---|
| MLP | 296 586 | 81.5 % | 83.5 % | 81.5 % | 80.4 % | 22 | 21 s | 1.11 ms |
| CNN | 356 234 | 92.3 % | 92.7 % | 92.3 % | 92.1 % | 40 | 52 s | 2.05 ms |

Modelo exportado a la demo: **CNN** (elegido por exactitud en validación: MLP 96.4 %, CNN 100.0 %).

## 3. Métricas por clase — CNN

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| Redonda | 78.7 % | 98.7 % | 87.6 % | 75 |
| Blanca | 98.6 % | 93.3 % | 95.9 % | 75 |
| Negra | 98.6 % | 93.3 % | 95.9 % | 75 |
| Corchea | 87.0 % | 89.3 % | 88.2 % | 75 |
| Silencio de negra | 94.8 % | 97.3 % | 96.1 % | 75 |
| Silencio de blanca | 98.6 % | 93.3 % | 95.9 % | 75 |
| Clave de sol | 90.6 % | 64.0 % | 75.0 % | 75 |
| Clave de fa | 91.5 % | 100.0 % | 95.5 % | 75 |
| Sostenido | 91.1 % | 96.0 % | 93.5 % | 75 |
| Bemol | 97.3 % | 97.3 % | 97.3 % | 75 |

## 4. Métricas por clase — MLP

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| Redonda | 93.8 % | 100.0 % | 96.8 % | 75 |
| Blanca | 87.1 % | 36.0 % | 50.9 % | 75 |
| Negra | 63.3 % | 92.0 % | 75.0 % | 75 |
| Corchea | 72.3 % | 97.3 % | 83.0 % | 75 |
| Silencio de negra | 100.0 % | 73.3 % | 84.6 % | 75 |
| Silencio de blanca | 72.5 % | 88.0 % | 79.5 % | 75 |
| Clave de sol | 82.5 % | 62.7 % | 71.2 % | 75 |
| Clave de fa | 98.7 % | 98.7 % | 98.7 % | 75 |
| Sostenido | 79.4 % | 66.7 % | 72.5 % | 75 |
| Bemol | 85.2 % | 100.0 % | 92.0 % | 75 |

## 5. Matriz de confusión — CNN (filas = clase real, columnas = predicción)

| Real \ Pred | Red | Bla | Neg | Cor | SNe | SBl | CSo | CFa | Sos | Bem |
|---|---|---|---|---|---|---|---|---|---|---|
| Red | 74 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Bla | 5 | 70 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Neg | 0 | 0 | 70 | 0 | 0 | 0 | 5 | 0 | 0 | 0 |
| Cor | 1 | 0 | 1 | 67 | 0 | 0 | 0 | 6 | 0 | 0 |
| SNe | 0 | 0 | 0 | 2 | 73 | 0 | 0 | 0 | 0 | 0 |
| SBl | 5 | 0 | 0 | 0 | 0 | 70 | 0 | 0 | 0 | 0 |
| CSo | 4 | 1 | 0 | 8 | 4 | 0 | 48 | 1 | 7 | 2 |
| CFa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 75 | 0 | 0 |
| Sos | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 72 | 0 |
| Bem | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 73 |

Abreviaturas: Red = Redonda, Bla = Blanca, Neg = Negra, Cor = Corchea, SNe = Silencio de negra, SBl = Silencio de blanca, CSo = Clave de sol, CFa = Clave de fa, Sos = Sostenido, Bem = Bemol.

## 6. Pares más confundidos (CNN)

| Clase real | Predicha como | Casos |
|---|---|---|
| Clave de sol | Corchea | 8 |
| Clave de sol | Sostenido | 7 |
| Corchea | Clave de fa | 6 |
| Silencio de blanca | Redonda | 5 |
| Negra | Clave de sol | 5 |
| Blanca | Redonda | 5 |

## 7. Configuración

| Parámetro | Valor |
|---|---|
| Entrada | 32x32x1, valores 0–1 |
| Optimizador | Adam, lr inicial 0.001 (ReduceLROnPlateau x0.5) |
| Pérdida | categorical_crossentropy con label smoothing 0.1 |
| Épocas máximas | 40 (EarlyStopping, paciencia 8) |
| Tamaño de lote | 64 |
| Aumento | rotación ±9°, zoom ±12 %, desplazamiento ±8 %, ruido gaussiano σ=0.04 |
| Entrenamiento | demás integrantes (sin 'test_test'), ~82 % al azar |
| Validación | ~18 % al azar de los demás integrantes |
| Prueba | TODO lo de 'test_test' (integrante no visto) |
| Unidad de división | dibujo original (sus variantes aumentadas van juntas) |
| Semilla | 42 |
| TensorFlow / Keras | 2.21.0 / 3.13.2 |
