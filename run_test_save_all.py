
import time
import argparse
import csv

from pathlib import Path
from copy import copy

from src.model import HybridModel

PATH_DATA = Path("./data/generated-graphs/")
PATH_REPORTS = Path("./reports")
PATH_ERROR_REPORTS = Path("./error_reports")
PATH_LOG = Path("./log")
EPS = 1e-4

seed = 9999

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
        default=5
    )

    args = parser.parse_args()

    folder = args.folder_test
    n_replications = args.replications

    if n_replications <= 0:
        parser.error("--replications must be greater than 0")

    directory = PATH_DATA / folder

    if not directory.is_dir():
        parser.error(f"Directory not found: {directory}")

    local_now = time.localtime()
    formatted = time.strftime("%Y-%m-%d_%H:%M:%S", local_now)

    PATH_REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = PATH_REPORTS / f"report_{folder}_{formatted}.csv"

    fieldnames = [
        "n_verte_graph",
        "n_edges_graph",
        "replication",
        "tao",
        "execution_time",
        "steps_to_consensus"
    ]
    
    if not report_path.is_file():
        with report_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    PATH_ERROR_REPORTS.mkdir(parents=True, exist_ok=True)
    
    error_report_path = PATH_ERROR_REPORTS / f"error_report_{folder}_{formatted}.csv"

    fieldnames_error = [
        "name",
        "error"
    ]
    
    if not error_report_path.is_file():    
        with error_report_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames_error)
            writer.writeheader()

    
    
    status_execute_path = PATH_LOG / f"staus_execute_{folder}_{formatted}.log"
    if not status_execute_path.is_file():
        with status_execute_path.open("w", newline="", encoding="utf-8") as logfile:
            logfile.write(f"## Status execute {folder}\n")
            
    """
    Listed Files Test
    """        
            
    files = sorted(
        (int(f.name.split("_")[1].split(".")[0]), f) for f in directory.iterdir()
        if f.is_file()
    )
            
    graph_files = [fdir for _, fdir in files]

    if not graph_files:
        print(f"No graph files found in {directory}")
        return
    
    for file in graph_files:
        try:
            model = HybridModel.from_file(str(file))
            model.set_middle_tao()
            tao = model.get_tao()
            
            snaphot = model.snapshot()
            n_vertex = len(snaphot["nodes"]) 
            n_edges = len(snaphot["edges"])
            tao = model.get_tao()
            n_steps = None
            
            execution_times = []

            print("Start:", file.name)

            for i in range(n_replications):
                
                start_time = time.perf_counter()
                n_steps = len(model.find_consensus_steps(EPS))
                end_time = time.perf_counter()
                
                print(f"replication done: {i + 1}/{n_replications}")
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
            print("Done!", file.name)

            with report_path.open("a", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for i in range(len(execution_times)):
                    result = {
                        "n_verte_graph" : n_vertex,
                        "n_edges_graph" : n_edges,
                        "replication" : i,
                        "tao" : tao,
                        "execution_time" : execution_times[i],
                        "steps_to_consensus" : n_steps
                    }
                    writer.writerow(result)

            with status_execute_path.open("a", newline="", encoding="utf-8") as logfile:
                logfile.write(f"{file.name} Done!\n")

        except Exception as e:
            print(f"{file.name} Error: {e}")
            error = [{
                "name" : file.name,
                "error" : e
            }]
            with error_report_path.open("a", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames_error)
                writer.writerows(error)

    print("\nReport generated successfully!")
    print("Report location:", report_path)


if __name__ == "__main__":
    main()