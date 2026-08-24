"""
Author: Oscar Vargas Pabon
"""
import matplotlib.pyplot as plt

def do_plot(data,name:str="-_-")->None:
    for d in data:
        plt.plot(d)
    plt.title(name)
    plt.show()


def main():
    graph_iter,n,girth,indeg,outdeg,iter,seed = map(int, input().split())
    mec,er,rge=[],[],[]
    for _ in range(graph_iter):
        mec.append(list(map(float, input().split())))
        er.append(list(map(float, input().split())))
        rge.append(list(map(float, input().split())))
    do_plot(mec, "Mec")
    do_plot(er, "Er")
    do_plot(rge, "Range")
if (__name__ == "__main__"):
    main()