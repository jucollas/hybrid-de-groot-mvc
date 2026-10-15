
import time
import argparse
import csv

from pathlib import Path
from copy import copy

from src.model import HybridModel


PATH_DATA = Path("./data/generated-graphs/")
PATH_REPORTS = Path("./reports")


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid DeGroot opinion-network testing"
    )

    parser.add_argument(
        "--folder_test",
        help="Path to a folder with several test graph files",
        default="set_test_00"
    )

    parser.add_argument(
        "--replications",
        help="Number of times to repeat each experiment",
        type=int,
        default=10
    )

    args = parser.parse_args()

    folder = args.folder_test
    n_replications = args.replications

    if n_replications <= 0:
        parser.error("--replications must be greater than 0")

    directory = PATH_DATA / folder

    if not directory.is_dir():
        parser.error(f"Directory not found: {directory}")

    # Create the report directory if it does not exist.
    PATH_REPORTS.mkdir(parents=True, exist_ok=True)

    report_path = PATH_REPORTS / f"report_{folder}.csv"

    results = []

    graph_files = sorted(
        file for file in directory.iterdir()
        if file.is_file()
    )

    if not graph_files:
        print(f"No graph files found in {directory}")
        return

    for file in graph_files:
        model = HybridModel.from_file(str(file))

        # Generate tau once for this graph.
        model.generate_random_tao()

        sum_time = 0.0
        sum_steps = 0
        execution_times = []

        print("Start:", file.name)

        for i in range(n_replications):
            aux_model = copy(model)

            start_time = time.perf_counter()
            aux_model.find_consensus()
            end_time = time.perf_counter()

            execution_time = end_time - start_time

            execution_times.append(execution_time)
            sum_time += execution_time
            sum_steps += aux_model.get_len_step_to_consensus()

        avg_time = sum_time / n_replications
        avg_steps = sum_steps / n_replications

        min_time = min(execution_times)
        max_time = max(execution_times)

        tao = model.get_tao()

        print("Done!", file.name)
        print("Tao:", tao)
        print("Avg execution time:", avg_time)
        print("Avg steps to consensus:", avg_steps)

        results.append({
            "graph": file.name,
            "tao": tao,
            "replications": n_replications,
            "avg_execution_time": avg_time,
            "min_execution_time": min_time,
            "max_execution_time": max_time,
            "avg_steps_to_consensus": avg_steps
        })

    # Write the CSV report.
    fieldnames = [
        "graph",
        "tao",
        "replications",
        "avg_execution_time",
        "min_execution_time",
        "max_execution_time",
        "avg_steps_to_consensus"
    ]

    with report_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\nReport generated successfully!")
    print("Report location:", report_path)


if __name__ == "__main__":
    main()