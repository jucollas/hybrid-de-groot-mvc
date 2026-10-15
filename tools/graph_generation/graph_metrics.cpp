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
	auto dist=(n*1ll*n<=edges.size()+rad)?floyd_warshall(n,edges):all_pairs_sparse(n,edges);
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
	std::vector<std::vector<int>> g(n);
	for(const Edge<tedge> &e:edges)g[e.u].push_back(e.v);

	std::vector<int> topo;topo.reserve(n);
	std::vector<bool> us(n,0);
	std::function<void(int)> taux=[&](int nd)->void{
		us[nd]=1;for(int e:g[nd])if(!us[e])taux(e);
		topo.push_back(nd);
	};for(int i=0;i<n;++i)if(!us[i])taux(i);
	//std::cout << "dxdxdxd" << std::endl;
	for(int i=0;i<n;++i)us[i]=0;
	std::function<int(int)>c_ch=[&](int nd)->int{
		int res=1;us[nd]=1;
		for(int e:g[nd])if(!us[e])res+=c_ch(e);
		return res;
	};const int cmp=c_ch(topo.front());

	//std::cout << cmp << " ????? " << n << std::endl;
	return cmp==n;
}

template<typename tedge>
int efficient_diameter(const int n,const std::vector<Edge<tedge>> &edges){
	// only works for undirected graphs _____ XD
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
