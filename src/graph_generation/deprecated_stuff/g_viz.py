
from sys import stdin
from pyvis.network import Network

def main():
	print("Entra pythn")
	n,m=map(int,stdin.readline().split())
	opi=list(map(float,stdin.readline().split()))
	edg=[]
	for  _ in range(m):
		u,v,w=stdin.readline().split()
		u=int(u);v=int(v);w=float(w);
		edg.append((u,v,w))
	if(n>20):return;
	g=Network(directed=True)
	for i in range(n):
		g.add_node(i,label="%.5f"%(opi[i]))
	#print(g)
	for u,v,w in edg:
		g.add_edge(u,v,weight=w)
	#print(g)
	print(n,m)
	g.toggle_physics(False)
	g.show("mtest.html",notebook=False)




if __name__ == '__main__':
	main()