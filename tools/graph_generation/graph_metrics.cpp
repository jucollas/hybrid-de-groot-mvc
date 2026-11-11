/*
Author: Oscar Vargas Pabon

To test the graphs generated in their couple of metrics.
It is mostly implemented to check radius, diameter and strong connectivity of the graph.

n is assumed to be the amount of nodes.
m is assumed to be the amount of edges.
*/
#pragma once

#include<vector>
#include<list>
#include<utility>
#include<algorithm> // max-min definitions
#include<functional>
#include"graph.cpp"

template<typename tedge>
std::vector<std::vector<int>> floyd_warshall(const int n,const std::vector<Edge<tedge>> &edges){
	//calculates the distance measured as the amount of edges between all pair of nodes.
	const int inf=n*333;//O(n^3)
	std::vector<std::vector<int>> dist(n,std::vector<int>(n,inf));
	for(const Edge<tedge> &edg:edges)dist[edg.u][edg.v]=1;
	for(int i=0;i<n;++i)dist[i][i]=0;
	// This impl works as a fun fact: "Incorrect implementations of the Floyd–Warshall
    //  algorithm give correct solutions after three repeats" Ikumi Hide, Soh Kumabe and Takanori Maehara.
	// for(int xd=0;xd<3;++xd)
	for(int k=0;k<n;++k)for(int i=0;i<n;++i)for(int j=0;j<n;++j)
		dist[i][j]=std::min<int>(dist[i][j],dist[i][k]+dist[k][j]);
	return dist;
}
template<typename tedge>
std::vector<std::vector<int>> all_pairs_sparse(const int n,const std::vector<Edge<tedge>> &edges){
	//calculates the distance measured as the amount of edges between all pair of nodes.
	const int inf=n*333;//O(n(n+m))
	std::vector<std::vector<int>> g(n);
	for(const Edge<tedge> &e:edges)g[e.u].push_back(e.v);
	std::vector<std::vector<int>> all_dist(n,std::vector<int>(n,inf));
	for(int piv=0;piv<n;++piv){//just BFS starting from each node
		std::vector<int> &dist=all_dist[piv];dist[piv]=0;
		std::list<int> q={piv};while(!q.empty()){
			const int nd=q.front();q.pop_front();
			for(int e:g[nd])if(dist[e]==inf){
				dist[e]=dist[nd]+1;q.push_back(e);
			}
		}
	}return all_dist;
}

template<typename tedge>
std::pair<int,int> graph_metrics(const int n,const std::vector<Edge<tedge>> &edges){
	// retrieves both the diameter and the radius of the graph.
	int diam=-1,rad=n*333;
	// BFS from every node, O(n(n+m)), is never asymptotically worse than Floyd-Warshall O(n^3)
	auto dist=all_pairs_sparse(n,edges);
	/*for(int i=0;i<n;++i)for(int j=0;j<n;++j){
		if(dist[i][j]==5)std::cerr << i << " <-> " << j << std::endl;
	}*/
	for(int i=0;i<n;++i){
		int ac=-1;for(int j=0;j<n;++j){
			ac   =std::max<int>(ac   ,dist[i][j]);
			diam =std::max<int>(diam ,dist[i][j]);
		}rad=std::min<int>(rad,ac);
	} return {diam,rad};
}

template<typename tedge>
bool strongly_connected( const int n,const std::vector<Edge<tedge>> &edges){
	if(n<=0)return 1; // verifies in O(n+m) if the graph is strongly connected.
	// The graph is strongly connected iff node 0 reaches every node in G
	// and every node reaches node 0 (i.e. node 0 reaches every node in G^T).
	std::vector<std::vector<int>> g(n),gt(n);
	for(const Edge<tedge> &e:edges)g[e.u].push_back(e.v),gt[e.v].push_back(e.u);
	auto reaches_all=[&](const std::vector<std::vector<int>>&adj)->bool{
		std::vector<bool> us(n,0);std::vector<int> st={0};us[0]=1;int cnt=1;
		while(!st.empty()){ // iterative DFS, avoids stack overflow for large n
			const int nd=st.back();st.pop_back();
			for(int e:adj[nd])if(!us[e])us[e]=1,++cnt,st.push_back(e);
		} return cnt==n;
	};
	return reaches_all(g)&&reaches_all(gt);
}

template<typename tedge>
int efficient_diameter(const int n,const std::vector<Edge<tedge>> &edges){
	// only works for undirected graphs _____ XD
	// NOTE: repeated double-sweep BFS. It is exact on trees; on general graphs it only
	// returns a LOWER BOUND of the diameter.
	const int inf=n*333;//O(n+m)
	std::vector<std::vector<int>> g(n);
	for(const Edge<tedge> &e:edges)g[e.u].push_back(e.v);
	std::vector<int> dist(n);int piv=0;for(int sd=0;sd<5;++sd){
		for(int i=0;i<n;++i)dist[i]=inf*(i!=piv);
		std::list<int> q;q.push_front(piv);while(!q.empty()){
			const int nd=q.front();q.pop_front();
			for(int e:g[nd])if(dist[e]==inf){
				dist[e]=dist[nd]+1;q.push_back(e);
			}
		}

		for(int i=0;i<n;++i)if(dist[piv]<dist[i])piv=i;
		//piv=92;
		//std::cerr << piv << " ? " << dist[piv] << " __ _ _ _ __ _ _ _ _ " << dist[92] << " ? " << dist[82] << std::endl;
	}int diam=dist[piv];
	return diam;
}
