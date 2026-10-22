#!/usr/bin/env python3
"""
Visualizador de experimentos para algoritmos sobre grafos.

Estructura esperada:
reports/
  peso_01.csv
  peso_05.csv
  peso_10.csv

Cada CSV debe tener columnas similares a:
graph,tao,replications,avg_execution_time,min_execution_time,
max_execution_time,avg_steps_to_consensus

El peso fijo de las aristas se toma por defecto del nombre del CSV.
Ejemplo: peso_05.csv -> etiqueta "peso 05".
"""
from pathlib import Path
import re
import argparse
import pandas as pd
import matplotlib.pyplot as plt

REQUIRED_COLUMNS = {
    "graph",
    "avg_execution_time",
}

def parse_vertices(graph_name: str):
    """Extrae el número de vértices de nombres como test_100.txt."""
    match = re.search(r"(\d+)", Path(str(graph_name)).stem)
    return int(match.group(1)) if match else None

def load_experiments(folder: Path) -> pd.DataFrame:
    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No se encontraron archivos CSV en: {folder.resolve()}"
        )

    frames = []
    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path, skipinitialspace=True)
        except Exception as exc:
            print(f"[AVISO] No se pudo leer {csv_path.name}: {exc}")
            continue

        # Limpia espacios en los encabezados, por si vienen del exportador.
        df.columns = [str(c).strip() for c in df.columns]
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            print(f"[AVISO] {csv_path.name}: faltan columnas {sorted(missing)}; omitido.")
            continue

        df["vertices"] = df["graph"].astype(str).map(parse_vertices)
        df["source_file"] = csv_path.name
        # El archivo representa una condición de peso fijo.
        # Puedes reemplazar esta etiqueta por una columna real si la tienes.
        df["weight_setting"] = csv_path.stem.replace("_", " ")

        for col in [
            "tao", "replications", "avg_execution_time",
            "min_execution_time", "max_execution_time",
            "avg_steps_to_consensus",
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["vertices", "avg_execution_time"])
        frames.append(df)

    if not frames:
        raise ValueError(
            "No se pudo cargar ningún CSV válido. Verifica los encabezados "
            "y que existan columnas graph y avg_execution_time."
        )

    data = pd.concat(frames, ignore_index=True)
    data["vertices"] = data["vertices"].astype(int)
    return data.sort_values(["weight_setting", "vertices"])

def plot_metric(data: pd.DataFrame, metric: str, ylabel: str, output: Path):
    if metric not in data.columns:
        print(f"[AVISO] No existe la métrica '{metric}' en los CSV; no se graficará.")
        return

    plot_data = data.dropna(subset=[metric])
    if plot_data.empty:
        print(f"[AVISO] No hay datos válidos para '{metric}'.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    for setting, group in plot_data.groupby("weight_setting", sort=True):
        group = group.sort_values("vertices")
        ax.plot(
            group["vertices"], group[metric],
            marker="o", linewidth=2, markersize=5, label=setting
        )

    ax.set_title(f"Comparación de experimentos: {ylabel}")
    ax.set_xlabel("Número de vértices")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(title="Archivo / peso fijo")
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    print(f"Gráfica guardada: {output.resolve()}")
    plt.show()

def main():
    parser = argparse.ArgumentParser(
        description="Compara resultados CSV de experimentos sobre grafos."
    )
    parser.add_argument(
        "--input", type=Path, default=Path("reports"),
        help="Carpeta que contiene los CSV (por defecto: ./reports)"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results"),
        help="Carpeta para guardar tabla y gráficas (por defecto: ./results)"
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    data = load_experiments(args.input)

    # Tabla consolidada, ordenada por condición de peso y tamaño.
    preferred = [
        "weight_setting", "vertices", "graph", "tao", "replications",
        "avg_execution_time", "min_execution_time", "max_execution_time",
        "avg_steps_to_consensus", "source_file"
    ]
    columns = [c for c in preferred if c in data.columns]
    table = data[columns].copy()
    table = table.rename(columns={
        "weight_setting": "condicion_peso",
        "vertices": "vertices",
        "graph": "archivo_grafo",
        "tao": "tao",
        "replications": "repeticiones",
        "avg_execution_time": "tiempo_promedio_s",
        "min_execution_time": "tiempo_minimo_s",
        "max_execution_time": "tiempo_maximo_s",
        "avg_steps_to_consensus": "pasos_promedio_consenso",
        "source_file": "archivo_csv",
    })
    table_path = args.output / "tabla_comparativa.csv"
    table.to_csv(table_path, index=False)
    print(f"Tabla guardada: {table_path.resolve()}")
    print("\nResumen:")
    print(table.to_string(index=False))

    plot_metric(
        data, "avg_execution_time",
        "Tiempo promedio de ejecución (s)",
        args.output / "tiempo_promedio.png"
    )
    plot_metric(
        data, "avg_steps_to_consensus",
        "Pasos promedio hasta el consenso",
        args.output / "pasos_consenso.png"
    )

if __name__ == "__main__":
    main()
