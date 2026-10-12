"""
config.py
Parámetros del experimento.

Glosario rápido
---------------
N   : tamaño de entrada = cantidad de estudiantes almacenados en la estructura.
M   : cantidad de búsquedas aleatorias que se ejecutan dentro de UN bloque medido.
R   : número de repeticiones (corridas independientes) de cada medición.
"""
from pathlib import Path

# --- rutas
RAIZ = Path(__file__).resolve().parent
DIR_RESULTADOS = RAIZ / "resultados"
DIR_GRAFICAS = RAIZ / "graficas"
NOMBRE_CSV = "tiempos_ejecucion.csv"

# --- estudio 1: escalamiento con N
TAMANOS_N = [10, 100, 1_000, 5_000, 10_000, 20_000, 50_000, 100_000]
MODOS_ID = ("aleatorio", "ordenado")
ESTRUCTURAS = ("lista", "abb", "bmas")

# El ABB con IDs ordenados cuesta O(N^2) en construir (cada inserción recorre
# toda la cadena). Se limita N para que el experimento termine en tiempo razonable.
N_MAX_ABB_ORDENADO = 5_000
REPETICIONES = 5                 # R: corridas independientes por medición (datos nuevos en cada una)
TIEMPO_MINIMO_S = 1.0            # cada bloque medido debe durar >= 1 segundo
MARGEN_CALIBRACION = 1.20        # compensa variaciones entre calibracion y medicion final
M_BUSQUEDAS = None               # None -> M se calibra solo (>= 1 s). Un entero fija M.
UNIDADES_MAX = 2_000_000         # tope de seguridad para M / repeticiones internas
FACTOR_MAX_CALIBRACION = 10      # evita saltos enormes que dejan el proceso sin progreso visible
ORDEN_B = 32                     # orden del B+ (máx. hijos por nodo interno)
SEMILLA_BASE = 2024              # la corrida r usa la semilla SEMILLA_BASE + r

