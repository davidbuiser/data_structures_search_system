"""
experimento.py
Ejecuta los experimentos y escribe TODOS los tiempos crudos en un único CSV
(resultados/tiempos_ejecucion.csv). Ese CSV es la base de analisis.py y graficas.py.

Estudio ejecutado (columna 'estudio' del CSV):
    escalamiento_N    : lista vs ABB vs B+, IDs aleatorios y ordenados, N creciente.

Operaciones medidas:
    busqueda : M búsquedas aleatorias                    (unidad = 1 búsqueda)
    carga    : construir la estructura con N inserciones (unidad = 1 construcción)
    listado  : listar todos los estudiantes ordenados    (unidad = 1 listado)

Diseño metodológico:
  * Cada bloque cronometrado se calibra para durar >= 1 s (se repite la
    operación 'unidades' veces dentro del bloque). tiempo_por_unidad = bloque/unidades.
  * R corridas independientes: en cada corrida se generan datos NUEVOS (semilla
    SEMILLA_BASE + r) y consultas nuevas. Todas las estructuras reciben los mismos datos.
  * El orden de las estructuras dentro de cada corrida se baraja (reduce sesgo por
    deriva del sistema: calentamiento térmico, procesos de fondo...).
  * La generación de datos y de IDs NO se cronometra.

Uso:
    python src/experimento.py                    # experimento completo
    python src/experimento.py --rapido           # prueba de humo (segundos)
    python src/experimento.py --estudios N       # solo un estudio (N, M, orden_b)
    python src/experimento.py --reiniciar        # borra el CSV y empieza de cero
"""
import argparse
import csv
import json
import os
import platform
import random
import sys
import time
from datetime import datetime

import config
from cronometro import calibrar, medir
from estructuras import crear_estructura
from generador import generar_estudiantes, generar_ids_busqueda

COLUMNAS = ["estudio", "estructura", "modo_ids", "N", "orden_b", "M_solicitado",
            "operacion", "repeticion", "semilla", "unidades", "tiempo_bloque_s",
            "tiempo_por_unidad_s", "supera_1s", "altura"]


# --- bloques medidos
def _bloque_carga(clave, datos, orden_b, veces):
    est = None
    for _ in range(veces):          # incluye liberar la estructura anterior
        est = crear_estructura(clave, orden_b)
        est.cargar(datos)
    return est


def _bloque_busqueda(buscar, ids):
    for i in ids:
        buscar(i)


def _bloque_listado(est, veces):
    for _ in range(veces):
        est.listar_ordenado()


# --- utilidades
class EscritorCSV:
    def __init__(self, ruta, reiniciar):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        existe = ruta.exists() and not reiniciar
        self._f = open(ruta, "a" if existe else "w", newline="", encoding="utf-8")
        self._w = csv.DictWriter(self._f, fieldnames=COLUMNAS)
        if not existe:
            self._w.writeheader()

    def fila(self, **kw):
        kw["supera_1s"] = int(kw["tiempo_bloque_s"] >= 1.0)
        kw["tiempo_bloque_s"] = f"{kw['tiempo_bloque_s']:.9f}"
        kw["tiempo_por_unidad_s"] = f"{kw['tiempo_por_unidad_s']:.12e}"
        self._w.writerow(kw)

    def flush(self):
        self._f.flush()
        os.fsync(self._f.fileno())

    def cerrar(self):
        self._f.close()


def _log(msg):
    print(msg, flush=True)


def _ram_gb():
    try:
        with open("/proc/meminfo") as f:
            return round(int(f.readline().split()[1]) / 1024 / 1024, 2)
    except Exception:
        pass
    try:
        import psutil
        return round(psutil.virtual_memory().total / 1024 ** 3, 2)
    except Exception:
        return None


def _cpu():
    try:
        with open("/proc/cpuinfo") as f:
            for linea in f:
                if linea.startswith("model name"):
                    return linea.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()


def guardar_metadata(directorio, parametros):
    meta = {
        "fecha_inicio": datetime.now().isoformat(timespec="seconds"),
        "sistema_operativo": f"{platform.system()} {platform.release()}",
        "arquitectura": platform.machine(),
        "procesador": _cpu(),
        "nucleos_logicos": os.cpu_count(),
        "ram_gb": _ram_gb(),
        "python": sys.version.split()[0],
        "implementacion_python": platform.python_implementation(),
        "reloj": "time.perf_counter()",
        "parametros": parametros,
    }
    with open(directorio / "metadata_experimento.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    return meta


# --- calibración
def calibrar_estructura(clave, n, modo, orden_b, tmin, m_fijo):
    """Devuelve {'carga': c, 'busqueda': M, 'listado': c} con bloques >= tmin."""
    objetivo = tmin * config.MARGEN_CALIBRACION
    semilla = config.SEMILLA_BASE - 1               # datos de calibración (no se reportan)
    datos = generar_estudiantes(n, modo, semilla)
    ids = [e["id"] for e in datos]

    c_carga, est = calibrar(lambda v: (clave, datos, orden_b, v), _bloque_carga,
                            objetivo, maximo=config.UNIDADES_MAX,
                            factor_max=config.FACTOR_MAX_CALIBRACION)
    if m_fijo:
        m = m_fijo
    else:
        m, _ = calibrar(lambda v: (est.buscar, generar_ids_busqueda(ids, v, semilla)),
                        _bloque_busqueda, objetivo, inicial=100, maximo=config.UNIDADES_MAX,
                        factor_max=config.FACTOR_MAX_CALIBRACION)
    c_list, _ = calibrar(lambda v: (est, v), _bloque_listado, objetivo,
                         maximo=config.UNIDADES_MAX,
                         factor_max=config.FACTOR_MAX_CALIBRACION)
    return {"carga": c_carga, "busqueda": m, "listado": c_list}


# --- estudio 1: N
def estudio_escalamiento(esc, tamanos, modos, estructuras, reps, orden_b, tmin, m_fijo):
    for modo in modos:
        for n in tamanos:
            claves = [c for c in estructuras
                      if not (c == "abb" and modo == "ordenado"
                              and n > config.N_MAX_ABB_ORDENADO)]
            t0 = time.time()
            cal = {c: calibrar_estructura(c, n, modo, orden_b, tmin, m_fijo)
                   for c in claves}
            _log(f"[N] modo={modo:<9} N={n:<7} calibrado  "
                 + "  ".join(f"{c}:M={cal[c]['busqueda']}" for c in claves))

            for rep in range(reps):
                semilla = config.SEMILLA_BASE + rep
                datos = generar_estudiantes(n, modo, semilla)     # NO cronometrado
                ids = [e["id"] for e in datos]
                orden = list(claves)
                random.Random(semilla).shuffle(orden)             # orden aleatorio

                for clave in orden:
                    ob = orden_b if clave == "bmas" else ""
                    base = dict(estudio="escalamiento_N", estructura=clave,
                                modo_ids=modo, N=n, orden_b=ob, M_solicitado="",
                                repeticion=rep,
                                semilla=semilla)
                    est, t_c = medir(_bloque_carga, clave, datos, orden_b,
                                     cal[clave]["carga"])
                    consultas = generar_ids_busqueda(ids, cal[clave]["busqueda"], semilla)
                    _, t_b = medir(_bloque_busqueda, est.buscar, consultas)
                    _, t_l = medir(_bloque_listado, est, cal[clave]["listado"])

                    # verificación de correctitud (fuera del cronómetro)
                    lst = est.listar_ordenado()
                    assert len(est) == n and [e["id"] for e in lst] == sorted(ids)
                    assert est.buscar(ids[0]) is not None
                    h = est.altura()
                    h = "" if h is None else h

                    for op, t, u in (("carga", t_c, cal[clave]["carga"]),
                                     ("busqueda", t_b, cal[clave]["busqueda"]),
                                     ("listado", t_l, cal[clave]["listado"])):
                        esc.fila(operacion=op, unidades=u, tiempo_bloque_s=t,
                                 tiempo_por_unidad_s=t / u, altura=h, **base)
            esc.flush()
            _log(f"[N] modo={modo:<9} N={n:<7} listo ({time.time() - t0:.0f} s)")


# --- principal
def main(argv=None):
    p = argparse.ArgumentParser(description="Experimentos Lista vs ABB vs B+")
    p.add_argument("--estudios", nargs="+", choices=["N"], default=["N"])
    p.add_argument("--dir", default=str(config.DIR_RESULTADOS),
                   help="carpeta de salida (CSV + metadata)")
    p.add_argument("--rapido", action="store_true",
                   help="prueba de humo: pocos tamaños, 2 repeticiones, bloques de 0.05 s")
    p.add_argument("--reiniciar", action="store_true", help="borra el CSV previo")
    p.add_argument("--repeticiones", type=int, default=config.REPETICIONES)
    p.add_argument("--tiempo-minimo", type=float, default=config.TIEMPO_MINIMO_S)
    p.add_argument("--orden-b", type=int, default=config.ORDEN_B)
    p.add_argument("--m", type=int, default=config.M_BUSQUEDAS,
                   help="fija M (por defecto se calibra para durar >= tiempo mínimo)")
    p.add_argument("--tamanos", type=int, nargs="+", default=config.TAMANOS_N)
    a = p.parse_args(argv)

    if a.rapido:
        a.repeticiones, a.tiempo_minimo = 2, 0.05
        a.tamanos = [10, 100, 1000, 3000]
        config.N_MAX_ABB_ORDENADO = 3000

    from pathlib import Path
    salida = Path(a.dir)
    salida.mkdir(parents=True, exist_ok=True)
    esc = EscritorCSV(salida / config.NOMBRE_CSV, a.reiniciar)
    guardar_metadata(salida, {
        "tamanos_N": a.tamanos, "modos_ids": list(config.MODOS_ID),
        "estructuras": list(config.ESTRUCTURAS), "repeticiones": a.repeticiones,
        "tiempo_minimo_bloque_s": a.tiempo_minimo, "orden_b": a.orden_b,
        "M_fijo": a.m, "semilla_base": config.SEMILLA_BASE,
        "N_max_abb_ordenado": config.N_MAX_ABB_ORDENADO,
        "estudios_ejecutados": a.estudios,
    })

    t0 = time.time()
    if "N" in a.estudios:
        estudio_escalamiento(esc, a.tamanos, config.MODOS_ID, config.ESTRUCTURAS,
                             a.repeticiones, a.orden_b, a.tiempo_minimo, a.m)
    esc.cerrar()
    _log(f"Terminado en {time.time() - t0:.0f} s -> {salida / config.NOMBRE_CSV}")


if __name__ == "__main__":
    main()
