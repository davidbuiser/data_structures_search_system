"""Resume mediciones y controla valores atipicos con desviacion estandar."""
import argparse
from pathlib import Path

import pandas as pd


COLUMNAS_GRUPO = ["estudio", "estructura", "modo_ids", "N", "orden_b",
                  "M_solicitado", "operacion"]


def resumir(csv_entrada, csv_salida, salida_mediciones=None, sigma_umbral=2.0):
    datos = pd.read_csv(csv_entrada)
    if datos.empty:
        raise ValueError("El CSV de entrada esta vacio")

    grupos = datos.groupby(COLUMNAS_GRUPO, dropna=False)["tiempo_por_unidad_s"]
    datos["promedio_grupo_s"] = grupos.transform("mean")
    datos["desviacion_estandar_grupo_s"] = grupos.transform("std").fillna(0.0)
    datos["z_score"] = 0.0
    hay_desviacion = datos["desviacion_estandar_grupo_s"] > 0
    datos.loc[hay_desviacion, "z_score"] = (
        (datos.loc[hay_desviacion, "tiempo_por_unidad_s"]
         - datos.loc[hay_desviacion, "promedio_grupo_s"])
        / datos.loc[hay_desviacion, "desviacion_estandar_grupo_s"]
    )
    datos["es_outlier"] = datos["z_score"].abs() > sigma_umbral

    resumen = (datos.groupby(COLUMNAS_GRUPO, dropna=False)["tiempo_por_unidad_s"]
               .agg(ejecuciones="count", promedio_s="mean", desviacion_estandar_s="std")
               .reset_index())
    resumen["desviacion_estandar_s"] = resumen["desviacion_estandar_s"].fillna(0.0)
    sin_outliers = datos.loc[~datos["es_outlier"]]
    resumen_sin = (sin_outliers.groupby(COLUMNAS_GRUPO, dropna=False)["tiempo_por_unidad_s"]
                   .agg(promedio_sin_outliers="mean",
                        desviacion_sin_outliers="std")
                   .reset_index())
    resumen = resumen.merge(resumen_sin, on=COLUMNAS_GRUPO, how="left")
    resumen["desviacion_sin_outliers"] = resumen["desviacion_sin_outliers"].fillna(0.0)
    conteo = (datos.groupby(COLUMNAS_GRUPO, dropna=False)["es_outlier"]
              .agg(outliers_detectados="sum")
              .reset_index())
    resumen = resumen.merge(conteo, on=COLUMNAS_GRUPO, how="left")
    resumen["criterio_outlier"] = f"|z| > {sigma_umbral:g}"

    csv_salida.parent.mkdir(parents=True, exist_ok=True)
    resumen.to_csv(csv_salida, index=False)
    if salida_mediciones is not None:
        salida_mediciones.parent.mkdir(parents=True, exist_ok=True)
        datos.to_csv(salida_mediciones, index=False)
    print(f"Resumen guardado en {csv_salida}")
    if salida_mediciones is not None:
        print(f"Control de mediciones guardado en {salida_mediciones}")
    print(f"Outliers detectados: {int(datos['es_outlier'].sum())} de {len(datos)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=Path("resultados/tiempos_ejecucion.csv"))
    parser.add_argument("--salida", type=Path, default=Path("resultados/resumen_estadistico.csv"))
    parser.add_argument("--salida-mediciones", type=Path,
                        default=Path("resultados/mediciones_controladas.csv"))
    parser.add_argument("--sigma", type=float, default=2.0,
                        help="umbral de desviaciones estandar para marcar outliers")
    args = parser.parse_args()
    if args.sigma <= 0:
        parser.error("--sigma debe ser mayor que cero")
    resumir(args.entrada, args.salida, args.salida_mediciones, args.sigma)


if __name__ == "__main__":
    main()
