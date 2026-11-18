
import time
import argparse
import csv

from pathlib import Path
from functools import reduce

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

    args = parser.parse_args()

    folder = args.folder_test

    directory : Path = PATH_DATA / folder

    if not directory.is_dir():
        parser.error(f"Directory not found: {directory}")

    local_now = time.localtime()
    formatted = time.strftime("%Y-%m-%d_%H:%M:%S", local_now)

    PATH_REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = PATH_REPORTS / f"report_{folder}_{formatted}.csv"

    fieldnames = [
        "n_verte_graph",
        "n_edges_graph",
        "n_file",
        "tao",
        "execution_time",
        "build_alpha_steps",
        "build_tao_steps",
        "copy_all_steps"
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
                   
            
    folder = sorted(
        (int(f.name.split("_")[1].split(".")[0]), f) for f in directory.iterdir()
        if f.is_dir()
    )
            
    graph_folder : list[Path] = [fdir for _, fdir in folder]

    if not graph_folder:
        print(f"No graph folder found in {directory}")
        return
    
    for folder in graph_folder:
        files = sorted(
            (int(f.name.split("_")[2].split(".")[0]), f) for f in folder.iterdir()
            if f.is_file()
        )
        file_path : list[Path] = [file_path for _, file_path in files]
        print("Start: folder", folder.name)
        
        data : list[dict] = list()
        for file in file_path:
            #try:
            model = HybridModel.from_file(str(file))
            model.set_middle_tao()
            
            snaphot = model.snapshot()
            n_vertex = len(snaphot["nodes"]) 
            n_edges = len(snaphot["edges"])
            tao = model.get_tao()
                
            start_time = time.perf_counter()
            steps = model.find_consensus_steps(EPS)
            end_time = time.perf_counter()

            n_file = int(file.name.split("_")[2].split(".")[0])
            print(f"End test: {n_file + 1}/{len(file_path)}")
            
            execution_time = end_time - start_time

            data.append({
                "n_verte_graph" : n_vertex,
                "n_edges_graph" : n_edges,
                "n_file" : n_file,
                "tao" : tao,
                "execution_time" : execution_time,
                "build_alpha_steps" : len(steps["build_alpha"]),
                "build_alpha_communications" : reduce(lambda acc, t : acc + len(t), steps["build_alpha"], 0),
                "build_tao_steps" : len(steps["build_tao"]),
                "build_tao_communications" : reduce(lambda acc, t : acc + len(t), steps["build_tao"], 0),
                "copy_all_steps" : len(steps["copy_all"]),
                "copy_all_communications" : reduce(lambda acc, t : acc + len(t), steps["copy_all"], 0),
            })

            """except Exception as e:
                print(f"{file.name} Error: {e}")
                error = [{
                    "name" : file.name,
                    "error" : e
                }]
                with error_report_path.open("a", newline="", encoding="utf-8") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames_error)
                    writer.writerows(error)"""

        print("Done!", folder.name)

        with report_path.open("a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)

        with status_execute_path.open("a", newline="", encoding="utf-8") as logfile:
            logfile.write(f"{file.name} Done!\n")

    print("\nReport generated successfully!")
    print("Report location:", report_path)


if __name__ == "__main__":
    main()