"""
cronometro.py
Medición de tiempos.

- medir():    cronometra UNA llamada con time.perf_counter (reloj monotónico de
              mayor resolución de Python) y apaga el recolector de basura
              mientras se mide, para quitar pausas aleatorias del GC.
- calibrar(): busca cuántas unidades de trabajo (búsquedas, construcciones o
              listados) hacen falta para que el bloque dure >= tiempo_minimo.
              Esa corrida de calibración también sirve de calentamiento y NO
              se guarda en los resultados.
"""
import gc
import math
import time


def medir(funcion, *args):
    """Ejecuta funcion(*args). Devuelve (resultado, segundos)."""
    gc.collect()
    gc.disable()
    try:
        inicio = time.perf_counter()
        resultado = funcion(*args)
        fin = time.perf_counter()
    finally:
        gc.enable()
    return resultado, fin - inicio


def calibrar(preparar, ejecutar, tiempo_minimo=1.0, inicial=1, maximo=10_000_000,
             factor_max=10):
    """
    preparar(c) -> tupla de argumentos para un bloque de c unidades (NO se cronometra).
    ejecutar(*args) -> trabajo que se cronometra.

    Devuelve (c, ultimo_resultado) con c = unidades por bloque tal que
    el bloque dura >= tiempo_minimo (o se alcanzó 'maximo').
    """
    c = max(1, inicial)
    while True:
        resultado, t = medir(ejecutar, *preparar(c))
        if t >= tiempo_minimo or c >= maximo:
            return c, resultado
        estimado = math.ceil(c * tiempo_minimo * 1.15 / max(t, 1e-9))
        c = min(maximo, max(c + 1, min(estimado, c * factor_max)))
