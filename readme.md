# Sistema de búsqueda de estudiantes

## Problema y objetivo

Una institución educativa necesita insertar, buscar por ID y listar ordenadamente registros con `id`, `nombre`, `edad` y `promedio`.

El objetivo es comparar experimentalmente una lista de Python, un árbol binario de búsqueda (ABB) y un árbol B+ cuando aumenta `N` y cambia el orden de inserción.

## Estructuras y complejidades

| Estructura    | Insertar             | Buscar              | Listar ordenado | Observación                        |
|---------------|----------------------|---------------------|-----------------|------------------------------------|
| Lista         | `O(1)` amortizado    | `O(N)`              | `O(N log N)`    | Recorrido secuencial.              |
| ABB aleatorio | promedio `O(log N)`  | promedio `O(log N)` | `O(N)`          | No tiene balanceo.                 |
| ABB ordenado  | `O(N)` por inserción | `O(N)`              | `O(N)`          | Se degenera en una cadena.         |
| B+            | `O(log_B N)`         | `O(log_B N)`        | `O(N)`          | Hojas enlazadas y nodos divididos. |

El ABB guarda una clave por nodo y usa recorrido inorden. El B+ guarda los registros en hojas, usa claves guía en nodos internos y el parámetro `orden_b` define el máximo de hijos por nodo.

## Entorno y versión evaluada

- Python 3.13.3, CPython; Windows 10; AMD64.
- Procesador: Intel i5 6th Model 78 Stepping 3.
- 4 núcleos lógicos y 7.88 GB de RAM.
- Fecha de la corrida oficial: 2026-10-12, 08:46:01.
- Reloj: `time.perf_counter()`.
- Dependencias: `numpy`, `pandas`, `matplotlib`, `psutil`.
- Metadatos completos: `resultados/metadata_experimento.json`.

## Metodología

### Datos y consultas

`generador.py` crea IDs únicos desde 1000 y registros con nombre, edad entre 17 y 30 y promedio entre 0.0 y 10.0. La semilla base es 2024; la repetición `r` usa `2024 + r`.

Se comparan dos órdenes de inserción: `aleatorio`, una permutación de los mismos IDs, y `ordenado`, IDs crecientes. Todas las estructuras reciben los mismos datos dentro de cada repetición.

Las consultas se generan con `random.choices`, muestreo uniforme con reemplazo entre IDs existentes. Por eso son aciertos; la misma consulta puede repetirse. Generar datos y consultas no hace parte del tiempo medido.

### Estudio principal: escalamiento con N

`N = 10, 100, 1000, 5000, 10000, 20000, 50000, 100000`; IDs aleatorios y ordenados; operaciones de carga, búsqueda y listado. El ABB ordenado se limita a `N=5000` porque construirlo cuesta aproximadamente `O(N^2)`.

La corrida oficial usa 5 repeticiones por combinación. El CSV histórico conserva 760 filas, incluidas mediciones adicionales que no se regeneran.

### Medición y estadística

`cronometro.py` usa `time.perf_counter()`, ejecuta `gc.collect()` y desactiva temporalmente el recolector durante el bloque medido. Se mide solo la operación; la generación queda fuera.

Los bloques se calibran hacia `TIEMPO_MINIMO_S=1.0`, con margen `1.20`. `UNIDADES_MAX=2_000_000` evita ejecuciones ilimitadas. El CSV registra unidades, tiempo total, tiempo por unidad, indicador `supera_1s` y altura.

`analisis.py` calcula por grupo el número de ejecuciones, promedio y desviación estándar de `tiempo_por_unidad_s`. El control de outliers usa `z = (x - promedio) / desviación_estándar` y marca como atípica cada medición con `|z| > 2`. Genera `resultados/mediciones_controladas.csv` con la marca, el promedio del grupo, la desviación y el puntaje z. También agrega al resumen el número de atípicos y el promedio recalculado sin ellos. `graficas.py` usa ese promedio y esa desviación para dibujar barras de error de `±1σ`. El criterio puede explorarse con `py analisis.py --sigma 1.5`, pero el resultado oficial usa `2σ`.

Los atípicos no se borran del CSV crudo: se conservan para trazabilidad y se marcan en el archivo controlado. En la corrida oficial se detectaron 0 de 760 mediciones con `|z| > 2`; el máximo `|z|` fue aproximadamente `1.786`. Esto debe interpretarse con cautela porque cada grupo tiene solo cinco repeticiones y la regla de `2σ` es conservadora para muestras pequeñas. El promedio sin atípicos es una estadística auxiliar y no reemplaza automáticamente al promedio oficial. Los resultados se interpretan considerando procesos de fondo, caché, memoria, calentamiento y mediciones muy pequeñas. Algunos bloques pequeños no superan un segundo por el tope de unidades y quedan marcados con `supera_1s=0`.

## Reproducción

Desde `Lab 3` en Windows:

```text
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py experimento.py --reiniciar
py analisis.py
py graficas.py
```

La corrida completa puede tardar varios minutos. Para ejecutar estudios por separado:

```text
py experimento.py --estudios N --reiniciar
```

Para una prueba corta: `py experimento.py --rapido --estudios N --reiniciar`. Sus resultados no deben mezclarse con los oficiales.

## Resultados e interpretación

Resultados entregados:

- `resultados/tiempos_ejecucion.csv`: mediciones crudas de la corrida histórica.
- `resultados/resumen_estadistico.csv`: ejecuciones, promedio, desviación y control estadístico; es la fuente de las barras de error.
- `resultados/mediciones_controladas.csv`: mediciones originales con z-score y marca de outlier.
- `resultados/metadata_experimento.json`: equipo, fecha y parámetros.
- `graficas/`: seis gráficas principales de escalamiento, con barras de error.

Las curvas se muestran con escalas logarítmicas y tiempos en milisegundos. Cada punto representa el promedio y su barra de error representa `promedio ± 1σ`. En general, los resultados siguen la teoría:

1. La Lista carga rápido, pero buscar crece linealmente.
2. El ABB aleatorio busca aproximadamente en `O(log N)` mientras su altura sea baja.
3. El ABB ordenado se vuelve una cadena: buscar es `O(N)` y cargar aproximadamente `O(N^2)`.
4. El B+ mantiene pocos niveles y lista eficientemente mediante sus hojas enlazadas.
5. Para `N` pequeño, llamadas de Python, objetos, diccionarios y medición producen overhead que puede ocultar las diferencias.
6. Las barras de error muestran la variabilidad de las cinco repeticiones mediante `±1σ`.

## Hallazgos principales

- La Lista es simple y barata para insertar, pero es la peor para buscar con `N` grande.
- El ABB aleatorio es eficiente, pero depende fuertemente del orden de entrada.
- El ABB ordenado demuestra por qué un ABB sin balanceo puede fallar en el peor caso.
- El B+ es más robusto ante el orden de inserción y especialmente adecuado para listados ordenados.
- Las complejidades predicen las tendencias, pero no determinan por sí solas los milisegundos de otro equipo.

## Limitaciones

El entorno no está aislado; las consultas son solo aciertos uniformes con reemplazo; no se midieron fallos ni distribuciones sesgadas; el ABB no representa un árbol balanceado; ABB ordenado solo llega a `N=5000`; algunos bloques pequeños no alcanzan un segundo por limitaciones físicas del hardware al aumentar todas las corridas experimentales; y el criterio `|z| > 2` es una regla de control, no una prueba de que una medición sea incorrecta. Las filas adicionales del CSV no forman parte de las gráficas actuales. No debe concluirse que una estructura es universalmente mejor ni que estos tiempos se transfieren sin cambios a otro computador.

## Verificación y uso de IA

Este proyecto se desarrolló con apoyo de **Claude (Anthropic) y GitHub Copilot** en dos etapas. Primero se exploraron los diversos árboles para comprender el problema; esa etapa se usó como base conceptual para las mediciones posteriores. Luego se realizó un proyecto con la base anterior de Lista, ABB y B+, añadiéndole la respectiva medición, el CSV y las gráficas reproducibles. Claude apoyó la etapa inicial; GitHub Copilot apoyó en VS Code la revisión de módulos, metodología, detección del `O(N^2)` del ABB degenerado, estadística, gráficas, validación y documentación.

Revisé código, depuré y ejecuté pruebas, además declaro que este trabajo es resultado de mi propio proceso de aprendizaje y que puedo explicar las estructuras, las mediciones y las conclusiones presentadas. Reconoceré las ideas, herramientas o materiales de terceros y no presentaré como propios datos, código o resultados que no haya generado o verificado. Conservaré los datos y parámetros necesarios para reproducir el experimento y reconoceré sus limitaciones.

Verifiqué que las tres estructuras insertan, buscan y listan los mismos IDs; que los listados son ascendentes; que las semillas reproducen datos; que `analisis.py` recalcula el CSV y marca los outliers; y que `graficas.py` regenera las figuras.

## Estructura del repositorio

```text
Lab 3/
|-- analisis.py
|-- config.py
|-- cronometro.py
|-- estructuras.py
|-- experimento.py
|-- generador.py
|-- graficas.py
|-- readme.md
|-- requirements.txt
|-- resultados/
|   |-- tiempos_ejecucion.csv
|   |-- resumen_estadistico.csv
|   |-- mediciones_controladas.csv
|   `-- metadata_experimento.json
`-- graficas/
    |-- escalamiento_aleatorio_busqueda.png
    |-- escalamiento_aleatorio_carga.png
    |-- escalamiento_aleatorio_listado.png
    |-- escalamiento_ordenado_busqueda.png
    |-- escalamiento_ordenado_carga.png
    `-- escalamiento_ordenado_listado.png
```