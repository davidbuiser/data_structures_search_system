"""
estructuras.py
Las tres estrategias de almacenamiento y búsqueda

    1. ListaEstudiantes -> lista sin ordenar, búsqueda lineal
    2. ABB              -> árbol binario de búsqueda (sin balanceo)
    3. ArbolBMas        -> árbol B+ (datos en hojas enlazadas)

Las tres cumplen la misma interfaz (EstructuraEstudiantes):

    insertar(estudiante)  -> agrega un registro
    cargar(estudiantes)   -> inserta un iterable de registros
    buscar(id)            -> registro o None
    listar_ordenado()     -> lista de registros en orden ascendente de ID
    altura()              -> niveles del árbol (None para la lista)
    len(estructura)       -> cantidad de registros

"""
from abc import ABC, abstractmethod
from bisect import bisect_left, bisect_right


class EstructuraEstudiantes(ABC):
    nombre = "base"

    @abstractmethod
    def insertar(self, estudiante): ...

    @abstractmethod
    def buscar(self, id_estudiante): ...

    @abstractmethod
    def listar_ordenado(self): ...

    @abstractmethod
    def altura(self): ...

    @abstractmethod
    def __len__(self): ...

    def cargar(self, estudiantes):
        for e in estudiantes:
            self.insertar(e)


# =====================================================================
# LISTA
# insertar O(1) | buscar O(N) | listar ordenado O(N log N)
# =====================================================================
class ListaEstudiantes(EstructuraEstudiantes):
    nombre = "Lista"

    def __init__(self):
        self._datos = []

    def insertar(self, estudiante):
        self._datos.append(estudiante)

    def buscar(self, id_estudiante):
        # Búsqueda lineal explícita (no se usa 'in' ni index()).
        for e in self._datos:
            if e["id"] == id_estudiante:
                return e
        return None

    def listar_ordenado(self):
        return sorted(self._datos, key=lambda e: e["id"])

    def altura(self):
        return None

    def __len__(self):
        return len(self._datos)


# =====================================================================
# ABB (sin balanceo). TODO es iterativo: con IDs ordenados el árbol se
# vuelve una cadena de profundidad N y la recursión de Python (~1000)
# fallaría.
# IDs aleatorios : altura ~ O(log N) -> insertar/buscar O(log N)
# IDs ordenados  : altura = N        -> insertar/buscar O(N)
# listar ordenado: O(N) (recorrido inorden)
# =====================================================================
class NodoABB:
    __slots__ = ("clave", "valor", "izq", "der")

    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izq = None
        self.der = None


class ABB(EstructuraEstudiantes):
    nombre = "ABB"

    def __init__(self):
        self.raiz = None
        self._tam = 0

    def insertar(self, estudiante):
        clave = estudiante["id"]
        nuevo = NodoABB(clave, estudiante)
        if self.raiz is None:
            self.raiz = nuevo
            self._tam = 1
            return
        actual = self.raiz
        while True:
            if clave < actual.clave:
                if actual.izq is None:
                    actual.izq = nuevo
                    break
                actual = actual.izq
            elif clave > actual.clave:
                if actual.der is None:
                    actual.der = nuevo
                    break
                actual = actual.der
            else:                       # ID repetido: se actualiza el registro
                actual.valor = estudiante
                return
        self._tam += 1

    def buscar(self, id_estudiante):
        actual = self.raiz
        while actual is not None:
            if id_estudiante == actual.clave:
                return actual.valor
            actual = actual.izq if id_estudiante < actual.clave else actual.der
        return None

    def listar_ordenado(self):
        """Inorden iterativo con pila explícita."""
        resultado, pila, actual = [], [], self.raiz
        while pila or actual is not None:
            while actual is not None:
                pila.append(actual)
                actual = actual.izq
            actual = pila.pop()
            resultado.append(actual.valor)
            actual = actual.der
        return resultado

    def altura(self):
        """Altura = número de niveles (recorrido por niveles, iterativo)."""
        if self.raiz is None:
            return 0
        nivel, h = [self.raiz], 0
        while nivel:
            h += 1
            nivel = [hijo for n in nivel for hijo in (n.izq, n.der)
                     if hijo is not None]
        return h

    def __len__(self):
        return self._tam


# =====================================================================
# ÁRBOL B+
# - Los registros viven SOLO en las hojas; los nodos internos guardan
#   claves-guía.
# - Las hojas están enlazadas (siguiente) -> listado y rangos rápidos.
# - 'orden' = máximo de hijos de un nodo interno (claves <= orden-1).
# Al desbordarse un nodo se divide y sube una clave al padre.
# insertar/buscar O(log N) | listar O(N) | rango O(log N + k)
# =====================================================================
class NodoBMas:
    __slots__ = ("es_hoja", "claves", "hijos", "valores", "siguiente")

    def __init__(self, es_hoja):
        self.es_hoja = es_hoja
        self.claves = []
        self.hijos = None if es_hoja else []       # solo nodos internos
        self.valores = [] if es_hoja else None     # solo hojas
        self.siguiente = None                      # solo hojas


class ArbolBMas(EstructuraEstudiantes):
    nombre = "B+"

    def __init__(self, orden=32):
        if orden < 3:
            raise ValueError("El orden del B+ debe ser >= 3")
        self.orden = orden
        self.max_claves = orden - 1
        self.raiz = NodoBMas(es_hoja=True)
        self._tam = 0

    # -------- utilidades internas
    def _buscar_hoja(self, clave, camino=None):
        nodo = self.raiz
        while not nodo.es_hoja:
            i = bisect_right(nodo.claves, clave)
            if camino is not None:
                camino.append((nodo, i))
            nodo = nodo.hijos[i]
        return nodo

    def _dividir_hoja(self, hoja):
        medio = len(hoja.claves) // 2
        nueva = NodoBMas(es_hoja=True)
        nueva.claves = hoja.claves[medio:]
        nueva.valores = hoja.valores[medio:]
        hoja.claves = hoja.claves[:medio]
        hoja.valores = hoja.valores[:medio]
        nueva.siguiente = hoja.siguiente
        hoja.siguiente = nueva
        return nueva.claves[0], nueva            # (clave que sube, nuevo nodo)

    def _dividir_interno(self, nodo):
        medio = len(nodo.claves) // 2
        clave_sube = nodo.claves[medio]
        nuevo = NodoBMas(es_hoja=False)
        nuevo.claves = nodo.claves[medio + 1:]
        nuevo.hijos = nodo.hijos[medio + 1:]
        nodo.claves = nodo.claves[:medio]
        nodo.hijos = nodo.hijos[:medio + 1]
        return clave_sube, nuevo

    # -------- operaciones públicas
    def insertar(self, estudiante):
        clave = estudiante["id"]
        camino = []
        hoja = self._buscar_hoja(clave, camino)

        pos = bisect_left(hoja.claves, clave)
        if pos < len(hoja.claves) and hoja.claves[pos] == clave:
            hoja.valores[pos] = estudiante       # ID repetido: se actualiza
            return
        hoja.claves.insert(pos, clave)
        hoja.valores.insert(pos, estudiante)
        self._tam += 1

        if len(hoja.claves) <= self.max_claves:
            return

        clave_sube, nuevo = self._dividir_hoja(hoja)
        izquierdo = hoja
        while camino:                            # propagar divisiones hacia arriba
            padre, i = camino.pop()
            padre.claves.insert(i, clave_sube)
            padre.hijos.insert(i + 1, nuevo)
            if len(padre.claves) <= self.max_claves:
                return
            clave_sube, nuevo = self._dividir_interno(padre)
            izquierdo = padre

        nueva_raiz = NodoBMas(es_hoja=False)     # se dividió la raíz: el árbol crece
        nueva_raiz.claves = [clave_sube]
        nueva_raiz.hijos = [izquierdo, nuevo]
        self.raiz = nueva_raiz

    def buscar(self, id_estudiante):
        hoja = self._buscar_hoja(id_estudiante)
        pos = bisect_left(hoja.claves, id_estudiante)
        if pos < len(hoja.claves) and hoja.claves[pos] == id_estudiante:
            return hoja.valores[pos]
        return None

    def buscar_rango(self, id_min, id_max):
        """Estudiantes con id_min <= id <= id_max (ventaja propia del B+)."""
        resultado = []
        hoja = self._buscar_hoja(id_min)
        while hoja is not None:
            for c, v in zip(hoja.claves, hoja.valores):
                if c > id_max:
                    return resultado
                if c >= id_min:
                    resultado.append(v)
            hoja = hoja.siguiente
        return resultado

    def listar_ordenado(self):
        nodo = self.raiz
        while not nodo.es_hoja:
            nodo = nodo.hijos[0]
        resultado = []
        while nodo is not None:
            resultado.extend(nodo.valores)
            nodo = nodo.siguiente
        return resultado

    def altura(self):
        h, nodo = 1, self.raiz
        while not nodo.es_hoja:
            nodo = nodo.hijos[0]
            h += 1
        return h

    def __len__(self):
        return self._tam

# Registro y fábrica (así el experimento no depende de clases concretas)

REGISTRO = {
    "lista": lambda orden_b: ListaEstudiantes(),
    "abb":   lambda orden_b: ABB(),
    "bmas":  lambda orden_b: ArbolBMas(orden=orden_b),
}


def crear_estructura(clave, orden_b=32):
    return REGISTRO[clave](orden_b)
