"""Genera graficas con promedios y desviaciones estandar."""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter


COLORES = {"lista": "#d95f02", "abb": "#1b9e77", "bmas": "#7570b3"}
NOMBRES = {"lista": "Lista", "abb": "ABB", "bmas": "B+"}


def _formato_decimal(valor, posicion):
    """Muestra los ticks sin notacion cientifica, incluso en escala logaritmica."""
    return f"{valor:.6f}".rstrip("0").rstrip(".")


def _guardar(figura, salida, nombre):
    salida.mkdir(parents=True, exist_ok=True)
    figura.tight_layout()
    figura.savefig(salida / nombre, dpi=160)
    plt.close(figura)


def _errorbar(eje, x, promedio, desviacion, etiqueta, color):
    """Dibuja promedio +/- desviacion, evitando limites inferiores no positivos."""
    promedio = promedio.to_numpy()
    desviacion = desviacion.fillna(0).to_numpy()
    error_inferior = desviacion.clip(max=promedio * 0.999999)
    eje.errorbar(
        x, promedio,
        yerr=[error_inferior, desviacion],
        marker="o", capsize=3, linewidth=1,
        label=etiqueta, color=color,
    )


def graficar(csv_path, salida):
    datos = pd.read_csv(csv_path)
    if datos.empty:
        raise ValueError(f"El CSV esta vacio: {csv_path}")

    resumen_path = csv_path.with_name("resumen_estadistico.csv")
    if not resumen_path.exists():
        raise FileNotFoundError(
            f"No existe el resumen estadistico requerido: {resumen_path}"
        )
    resumen_estadistico = pd.read_csv(resumen_path)
    resumen_estadistico["promedio_ms"] = resumen_estadistico["promedio_s"] * 1000
    resumen_estadistico["desviacion_ms"] = (
        resumen_estadistico["desviacion_estandar_s"].fillna(0) * 1000
    )
    n = datos[datos["estudio"] == "escalamiento_N"]
    for modo in sorted(n["modo_ids"].dropna().unique()):
        for operacion, nombre in (("busqueda", "busqueda"),
                                  ("carga", "carga"),
                                  ("listado", "listado")):
            figura, eje = plt.subplots(figsize=(8, 5))
            muestra = resumen_estadistico[
                (resumen_estadistico["estudio"] == "escalamiento_N")
                & (resumen_estadistico["modo_ids"] == modo)
                & (resumen_estadistico["operacion"] == operacion)
            ]
            for clave, grupo in muestra.groupby("estructura"):
                _errorbar(
                    eje, grupo["N"], grupo["promedio_ms"], grupo["desviacion_ms"],
                    NOMBRES.get(clave, clave), COLORES.get(clave),
                )
                eje.set(title=f"{nombre.title()} por N - IDs {modo}",
                    xlabel="N (estudiantes)", ylabel="Tiempo promedio por unidad (ms)")
            eje.set_xscale("log")
            eje.set_yscale("log")
            eje.xaxis.set_major_formatter(FuncFormatter(_formato_decimal))
            eje.yaxis.set_major_formatter(FuncFormatter(_formato_decimal))
            eje.grid(True, which="both", alpha=0.25)
            eje.legend(title="Estructura")
            _guardar(figura, salida, f"escalamiento_{modo}_{nombre}.png")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("resultados/tiempos_ejecucion.csv"))
    parser.add_argument("--salida", type=Path, default=Path("graficas"))
    args = parser.parse_args()
    graficar(args.csv, args.salida)
    print(f"Graficas guardadas en {args.salida}")


if __name__ == "__main__":
    main()