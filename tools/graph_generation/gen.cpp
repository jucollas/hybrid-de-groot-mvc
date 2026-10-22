/* Author: Oscar Vargas Pabon
 ________
|    ___ |
|  ,',.(`|
| :  `'  |
| :) _  (|
|  `:_)_,|
|________|

This file contains functions to generate graphs and opinions. The graphs are generated
	as strongly connected components.
Opinion generation:
	- gen_opi(n) generates n random opinions in the range [0,1]
	- gen_lv_opi(n,edges) generates n opinions based on the communities of the directed louvain method.
		The opinions are generated in a way that nodes in the same community have similar opinions.
		This is done by assigning a disjoint [l,r] range for each child of the louvain tree, where
		each $[l_i,r_i],[l_j,r_j]$ childs of a node have the same 'range size'.
Graph generation:
	- gen_scg(n,p,girth) generates a strongly connected component with n nodes, 
			where each edge is added with probability p. It starts with a cycle of length girth,
			then each iteration adds a new node. It ensures a incoming connection and an outgoing connection,
			which ensures strong connectivity is preserved. All other edges are added with probability p.
			It can be thought of as a variation of the Erdos-Renyi algorithm.
	- gen_barabasiAlbert_scg(n,ein,eout,girth) generates a strongly connected component using a variation of
			the Barabasi-Albert algorithm. The algorithms starts with a cycle of length girth. On each
			iteration, ein incoming edges and eout outgoing edges are added to the new node.
			All nodes are selected with probability proportional to their out-degree. Assuming
			ein,eout>0 the graph preserves strong connectivity. The algorithm runs in O(n*(ein+eout)*log(n)) time.
			It would be interesting to see a variation in which ein depends on the out-degree and eout
			depends on the in-degree.
	- gen_barAlb_trans(n) generates a strongly connected graph using a variation of gen_barabasiAlbert_scg.
			This was transcripted from lordRap's (Santiago Peña) repository.
	- kronecker_up(n,k,edge) generates the k-th kronecker product of the graph defined by edge.
			The output graph has n^k nodes and |edge|^k edges. The algorithm runs in O(|edge|*k) time.
			It preserves strong connectivity. It may not be very useful as the resulting graph may end up
			with weird structures. If needed, I may continue trying to implement stuff like this.
*/
#pragma once

#include "graph.cpp"
#include "louvain.cpp"
#include "graph_metrics.cpp"
#include<vector>
#include<cassert>
#include<functional>
#include<random>
#include<chrono>
const uint64_t seed=std::chrono::steady_clock::now().time_since_epoch().count();
//const uint64_t seed= 16516686549165;
std::mt19937 rng( seed );
std::uniform_real_distribution<double> raw_rng_dbl(0,1);
inline double rng_dbl(){return raw_rng_dbl(rng);}
inline int gen(int lim){return (lim+rng()%lim)%lim;};

/******************************************************************
 * Opinion generation functions
*******************************************************************/
std::vector<double> gen_opi(int n){
	// all opinions are on the range [0,1]
	std::vector<double> res(n);for(double &ac:res)ac=rng_dbl();
	return res;
}
std::vector<double> gen_lv_opi(int n,const std::vector<Edge<double>>&edges){
	auto m_rng_dbl=[&](double l,double r)->double{
		std::uniform_real_distribution<double> my_raw_rng_dbl(l,r);
		return my_raw_rng_dbl(rng);
	};
	//for(auto e:edges)assert(e.w==0.);//was failing xd
	LTree *rt=di_louvain<double>(n,edges);
	//std::cerr << "all the same " << rt->child.size() << '\n';
	std::vector<double> opi(n,-1);
	std::function<void(LTree*,double,double)>dfs=[&](LTree*nd,double l,double r)->void{
		if(nd->node!=-1)opi[nd->node]=m_rng_dbl(l,r);
		//if(nd->node!=-1)std::cerr << l << ' ' << r << ' ' << opi[nd->node] << std::endl;
		double prt=(r-l)/double(nd->child.size()),x=l;
		for(LTree*c:nd->child)dfs(c,x,x+prt),x+=prt;
	};dfs(rt,0,1);delete(rt);
	return opi;
}

void gen_edge_same_weight(int n, std::vector<Edge<double>>&edges, const double minima){
	for(Edge<double> & ac : edges) ac.w = minima;
}
/******************************************************************
	* Edge weight generation functions
********************************************************************/
void gen_edges_with_minima(int n, std::vector<Edge<double>>&edges,const double minima){
	// generates edge-weights on ranges [minima,1] such that
	// $min_e\{w_e}\=minima$ and the sum doesnt excede 1
	std::vector<double> norm(n,0);
	for(int i=0;i<n;++i)norm[i]=rng_dbl();//for self-influence
	for(Edge<double>&ac:edges)ac.w=rng_dbl();

	std::vector<int> in_deg(n,0);
	for(Edge<double>&ac:edges)in_deg[ac.v]++,norm[ac.v]+=ac.w;
	for(Edge<double>&ac:edges)ac.w=ac.w*(1.-in_deg[ac.v]*minima)/norm[ac.v]+minima;
	if(minima>0.)edges[gen(edges.size())].w=minima;
}
inline void gen_edges(int n,std::vector<Edge<double>>&edges){
	gen_edges_with_minima(n,edges,0);
}

/******************************************************************
 * Graph generation functions
*******************************************************************/
std::vector<Edge<double>> gen_scg(int n,double p,int girth=3){
	// generates a strongly connected component. Each edge is added with 
	// Probability p
	assert(n>=girth);
	std::vector<Edge<double>> res;
	for(int i=0;i<n;++i)res.emplace_back(i,i,rng_dbl());//self-edges
	for(int i=0;i<girth;++i)res.emplace_back(i?i-1:girth-1,i,rng_dbl());
	for(int i=girth;i<n;++i){
		int in=rng()%i,out=rng()%i;
		for(int j=0;j<i;++j)if(rng_dbl()<=p||j==in )res.emplace_back(j,i,rng_dbl());
		for(int j=0;j<i;++j)if(rng_dbl()<=p||j==out)res.emplace_back(i,j,rng_dbl());
	} // Now I have to deal with the weights ....
	std::vector<double> norm(n,0);for(Edge<double> &ac:res)norm[ac.v]+=ac.w;
	for(Edge<double> &ac:res)ac.w/=norm[ac.v];
	return res;
}

/*
function : gen_barabasiAlbert_scg
version: 2.0
*/
std::vector<Edge<double>> gen_barabasiAlbert_scg(
	const int n,const int ein,const int eout, const int girth=3){
	// n -> graph size ; ein -> expected in-degree ; eout -> expected out-degree ; girth -> beginning cycle
	assert(n>=girth); std::vector<Edge<double>> res;
	//for(int i=0;i<n;++i)res.emplace_back(i,i,rng_dbl());
	for(int i=0;i<girth;++i)res.emplace_back(i?i-1:girth-1,i,rng_dbl());
	
	std::vector<int> deg(n,0);

	std::vector<int> fenw(n+1,0);int f_tot=0;
	
	//std::vector<int> arr(n+1,0);
	auto update=[&](int x,int vl)->void{
		//arr[x]+=vl;
		assert(x>0);for(;x<=n;x+=x&-x)fenw[x]+=vl;
	};
	auto query=[&](int x)->int{
		assert(x>=0);
		int rq=0;for(;x;x-=x&-x)rq+=fenw[x];
		return rq;
	};
	auto binlift=[&](int obj)->int{

		//std::cerr << f_tot << "???? here " << obj << std::endl;
		//std::cerr << "[arr]";for(int ac:arr)std::cerr <<' ' << ac; std::cerr << '\n';
		int ind=0,nx,e=1;while(e<=n)e<<=1;
		for(;e;e>>=1){
			nx=ind+e;if(nx<=n&&fenw[nx]<obj){
				obj-=fenw[nx];ind=nx;
			}
		}

		//std::cerr << obj << " asdfa " << ind << std::endl;
		return ind;
	};
	//std::cerr << "xdxd" << std::endl;
	for(int i=0;i<girth;++i)++f_tot,update(i+1,1),++deg[i];
	for(int i=girth;i<n;++i){
		const int prv=res.size();
		//std::cerr << "iteration regarding node " << i << std::endl;
		//std::cerr<<"[deg]";for(int i=0;i<n;++i)std::cerr << ' ' << deg[i];std::cerr << std::endl;
		//std::cerr<<"[fenw]";for(int i=0;i<=n;++i)std::cerr << ' ' << query(i);std::cerr << std::endl;
		for(int j=0;j<=ein&&f_tot>0;++j){
			int nd=binlift(gen(f_tot)+1); assert(nd<n);
			//std::cerr << "1_insert "<< nd << ", " << i << std::endl;
			res.emplace_back(nd,i,rng_dbl());

			//std::cerr<<"[fenw]";for(int i=0;i<=n;++i)std::cerr << ' ' << query(i);std::cerr << std::endl;
			//std::cerr<<"[deg]";for(int i=0;i<n;++i)std::cerr << ' ' << deg[i];std::cerr << std::endl;
			
			f_tot-=deg[nd]; update(nd+1,-deg[nd]); ++deg[nd];
		}
		for(int j=prv;j<int(res.size());++j){
			int u=res[j].u;
			f_tot+=deg[u],update(u+1,deg[u]);
		}
		//std::cerr<<"[deg]";for(int i=0;i<n;++i)std::cerr << ' ' << deg[i];std::cerr << std::endl;
		//std::cerr<<"[fenw]";for(int i=0;i<=n;++i)std::cerr << ' ' << query(i);std::cerr << std::endl;
		//exit(12);
		//std::cerr << "################## " << i << std::endl;
		const int prv2=res.size();
		for(int j=0;j<=eout&&f_tot>0;++j){
			int nd=binlift(gen(f_tot)+1);assert(nd<n);
			
			//std::cerr<<"[fenw]";for(int i=0;i<=n;++i)std::cerr << ' ' << query(i);std::cerr << std::endl;
			//std::cerr<<"[deg]";for(int i=0;i<n;++i)std::cerr << ' ' << deg[i];std::cerr << std::endl;
			
			//std::cerr << nd << " ??_? " << i << " aa " << deg[nd] << " _ " << f_tot << " * " << query(n) << std::endl;
			//std::cerr << "2_insert "<< i << ", " << nd << std::endl;
			res.emplace_back(i,nd,rng_dbl());
			
			f_tot-=deg[nd];update(nd+1,-deg[nd]); ++deg[i];

			
		} f_tot+=deg[i],update(i+1,deg[i]);
		for(int j=prv2;j<int(res.size());++j){
			int v=res[j].v;
			f_tot+=deg[v],update(v+1,deg[v]);
		}

	} // Normalize 
	//exit(1);
	//std::cerr << "?????" << std::endl;
	std::vector<double> norm(n,0);for(Edge<double> &ac:res)norm[ac.v]+=ac.w;
	for(Edge<double> &ac:res)ac.w/=norm[ac.v];
	return res;
}

std::vector<Edge<double>> gen_barAlb_trans(const int n){
	// a transcription from the following
	// https://github.com/Lordrap2002/opinion-model-maude/blob/main/generador.py
	std::vector<Edge<double>> res;while(!strongly_connected(n,res)){
		res.clear();
		//std::cout << "xxdxdxdxxxd" << std::endl;
		std::vector<int> N={0,1},deg(n,1);int tt=0;N.reserve(n);
		for(int x=2;x<n;++x){
			for (int y:N){
				// 
				//if(gen(tt+x+1)<deg[y]){
				if(rng_dbl()<double(deg[y])/double(tt+x+1)){
					//std::cout << "===????"<<std::endl;
					res.emplace_back(y,x,rng_dbl());
					++deg[y];++tt;
				}
				//if(gen(tt+x+1)<deg[x]){
				if(rng_dbl()<double(deg[x])/double(tt+x+1)){
					//std::cout << "===????"<<std::endl;
					res.emplace_back(x,y,rng_dbl());
					++deg[x];++tt;
				}
			}N.push_back(x);
		}
	}
	for(int i=0;i<n;++i)res.emplace_back(i,i,rng_dbl());

	std::vector<double> norm(n,0);for(Edge<double> &ac:res)norm[ac.v]+=ac.w;
	for(Edge<double> &ac:res)ac.w/=norm[ac.v];
	return res;
}
template<typename tedge>
std::vector<Edge<tedge>> kronecker_up(int n,int k,const std::vector<Edge<tedge>>&edge){
	// creates A=A(kronecker)A...(kronecker)A k times (kth kronecker product)
	// E:=|edge|
	// in time O(E*k) (linear to the output graph)
	// Note the graph has n^k nodes and E^k edges

	// Idea vaguely taken from:::::
	// Kronecker Graphs: An Approach to Modeling Networks
	// Leskovec et Al
	//for(const Edge<tedge>&e:edge)std::cerr << e.u << ' ' << e.v << ' ' << e.w << std::endl;
	std::vector<Edge<tedge>> redge;
	std::function<void(int,int,int,tedge)> dfs=[&](int ch,int i,int j,tedge acm)->void{
		 //std::cerr<<ch << ' ' << i << ' ' << j << ' ' << acm << std::endl;
		if(!ch){redge.emplace_back(i,j,acm);return;}
		for(const Edge<tedge>&e:edge) dfs(ch-1,i*n+e.u,j*n+e.v,acm*e.w);	
	};dfs(k,0,0,1.); return redge;
}
