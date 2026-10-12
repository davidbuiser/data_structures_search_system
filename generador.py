"""
generador.py
Generación de datos y de búsquedas.

Registro de estudiante:
    {"id": int, "nombre": str, "edad": int, "promedio": float}
"""
import random

NOMBRES = [
    "Ana", "Carlos", "María", "Luis", "Sofía", "Jorge", "Camila", "Andrés",
    "Valentina", "Diego", "Laura", "Felipe", "Daniela", "Santiago", "Paula",
    "Mateo", "Isabela", "Nicolás", "Juliana", "Sebastián",
]


def generar_estudiantes(n, modo="aleatorio", semilla=42, id_inicial=1000):
    """
    Genera n estudiantes con IDs únicos (id_inicial ... id_inicial+n-1).

    modo="ordenado"  -> se entregan en orden creciente de ID (caso peor del ABB).
    modo="aleatorio" -> los mismos IDs, entregados en orden aleatorio (permutación).
    """
    if modo not in ("ordenado", "aleatorio"):
        raise ValueError("modo debe ser 'ordenado' o 'aleatorio'")
    rng = random.Random(semilla)
    ids = list(range(id_inicial, id_inicial + n))
    if modo == "aleatorio":
        rng.shuffle(ids)
    return [
        {
            "id": i,
            "nombre": rng.choice(NOMBRES),
            "edad": rng.randint(17, 30),
            "promedio": round(rng.uniform(0.0, 10.0), 1),
        }
        for i in ids
    ]


def generar_ids_busqueda(ids, m, semilla):
    """
    M IDs de búsqueda: muestreo uniforme CON reemplazo entre los IDs existentes.
    Con la misma semilla, las primeras k búsquedas son idénticas para cualquier M,
    así todas las estructuras reciben la misma secuencia de consultas.
    """
    return random.Random(semilla).choices(ids, k=m)
