import argparse
import csv
import pandas as pd
import matplotlib.pyplot as plt



from pathlib import Path

def plot_dispert(df):

    plt.figure(figsize=(10, 6))

    plt.scatter(
        df["n_verte_graph"],
        df["execution_time"],
        alpha=0.5,
        color="blue",
        label="Execution Time"
    )

    plt.xlabel("Number of Vertices")
    plt.ylabel("Execution Time (seconds)")
    plt.title("Execution Time vs Number of Vertices")

    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_steps(data):
    plt.figure(figsize=(10, 6))

    plt.plot(data.index, data["min"],
            marker="o", color="blue", label="Steps")

    """plt.plot(all_stats.index, all_stats["max"],
            marker="o", color="red", label="Maximum Time")

    plt.plot(all_stats.index, all_stats["min"],
            marker="o", color="green", label="Minimum Time")"""

    plt.xlabel("Number of Vertices")
    plt.ylabel("Execution Time (seconds)")
    plt.title("Execution Time vs Number of Vertices")

    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()

def plot_metric(all_stats):
    plt.figure(figsize=(10, 6))

    plt.plot(all_stats.index, all_stats["mean"],
            marker="o", color="blue", label="Average Time")

    plt.plot(all_stats.index, all_stats["max"],
            marker="o", color="red", label="Maximum Time")

    plt.plot(all_stats.index, all_stats["min"],
            marker="o", color="green", label="Minimum Time")

    plt.xlabel("Number of Vertices")
    plt.ylabel("Execution Time (seconds)")
    plt.title("Execution Time vs Number of Vertices")

    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()

def main():
    parser = argparse.ArgumentParser(
        description="convert to compress data"
    )
    
    parser.add_argument(
        "--input_file", type=Path,
        help = "File to convert"
    )
    
    args = parser.parse_args()
    
    input_file = args.input_file
    output_file = Path(input_file.stem + "_compress" + input_file.suffix)
    
    fieldnames = [
        "n_vertex",
        "n_edges",
        "replications",
        "avg_execution_time",
        "min_execution_time",
        "max_execution_time",
        "steps_to_consensus"
    ]
    
    
    
    with output_file.open("a", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
    try: 
        df = pd.read_csv(input_file)
    except Exception as exc:
        raise RuntimeError(f"Error : {exc}")
    #print(df.columns)
    df.columns = [str(c).strip() for c in df.columns]
    """avg_time = df.groupby("n_verte_graph")["execution_time"].mean()
    max_time = df.groupby("n_verte_graph")["execution_time"].max()
    min_time = df.groupby("n_verte_graph")["execution_time"].min()"""
    plot_dispert(df)
    all_stats = df.groupby("n_verte_graph")["execution_time"].agg(["mean", "max", "min"])
    plot_metric(all_stats)
    all_stats = df.groupby("n_edges_graph")["execution_time"].agg(["mean", "max", "min"])
    plot_metric(all_stats)
    
    steps_to_consensus = df.groupby("n_verte_graph")["steps_to_consensus"].agg(["min"])#.agg(["mean", "max", "min"])
    print(steps_to_consensus)
    plot_steps(steps_to_consensus)
    
    
    
        
    
    
     
    

if __name__ == "__main__":
    main()