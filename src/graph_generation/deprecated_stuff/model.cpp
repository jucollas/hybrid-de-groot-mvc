/*
Author:Oscar Vargas Pabon
*/
#pragma once

#include<bits/stdc++.h>
#include<cassert>
#include"graph.cpp"

template <typename tmod, 
const std::function<std::vector<int>(const std::vector<tmod>&,const std::vector<Edge<tmod>>&,const double) > &edge_selector,
bool normalize
>
struct Model{
	std::vector<tmod> opinion; std::vector<Edge<tmod>> edge;
	
	// quality of life stuff
	Model(int n=0){opinion.clear();edge.clear();opinion.resize(n);}
	Model(const std::vector<tmod> &opi,const std::vector<Edge<tmod>>&edg):opinion(opi),edge(edg){};
	
	void add_edge(int u,int v,tmod w){
		// Adds an edge u->v W(u,v)=w
		const int eind=edge.size();
		edge.emplace_back(u,v,w);
	}
	void mod_opinion(const std::vector<tmod> &opi){opinion=opi;}
	
	static bool check_eps_conv(const std::vector<tmod> &opi, const double EPS ){
		tmod mini=2,maxi=-1;for(const tmod &ac:opi)mini=std::min(mini,ac),maxi=std::max(maxi,ac);
		return maxi-mini <= EPS;
	}
	std::vector<std::vector<tmod>> sim_opi(int iter,const double EPS=1e-2)const{
		std::vector<std::vector<tmod>> res;
		std::vector<tmod> aopi=opinion,nopi,normi(opinion.size(),1);
		int time=0,communication=0; while(time<iter){
			nopi=aopi; res.push_back(aopi);
			std::vector<int> aedge=edge_selector(aopi,edge,EPS);
			
			if(normalize){
				std::fill(normi.begin(),normi.end(),0);
				for(int eind:aedge)normi[edge[eind].v]+=edge[eind].w;
			}
			
			for(int eind:aedge){
				int u=edge[eind].u,v=edge[eind].v; tmod w=edge[eind].w/normi[v];
				// std::cout << edge[eind].w<< " __ __ _ _ __ _ " << w << std::endl;
				nopi[v]+=(aopi[u]-aopi[v])*w;
			}
			
			std::swap(nopi,aopi);++time;communication+=aedge.size();
		}
		// for(tmod ac:aopi)std::cout << ac << ' '; std::cout << std::endl;
		// for(tmod ac:normi)std::cout << ac << ' '; std::cout << std::endl;
		return res;
	}
	std::tuple<int,int,double,double> sim( const double EPS=1e-2, const int max_iter=1e9+333 ) const {
		
		std::vector<tmod> aopi=opinion,nopi,normi(opinion.size(),1);
		int time=0,communication=0; while(!check_eps_conv(aopi,EPS)&&time<max_iter){
			nopi=aopi;
			std::vector<int> aedge=edge_selector(aopi,edge,EPS);
			
			if(normalize){
				std::fill(normi.begin(),normi.end(),0);
				for(int eind:aedge)normi[edge[eind].v]+=edge[eind].w;
			}
			
			for(int eind:aedge){
				int u=edge[eind].u,v=edge[eind].v; tmod w=edge[eind].w/normi[v];
				// std::cout << edge[eind].w<< " __ __ _ _ __ _ " << w << std::endl;
				nopi[v]+=(aopi[u]-aopi[v])*w;
			}
			
			std::swap(nopi,aopi);++time;communication+=aedge.size();
		}
		double mx_opi=-1,mn_opi=2;for(double ac:aopi)
			mx_opi=std::max<double>(mx_opi,ac),mn_opi=std::min<double>(mn_opi,ac);
		double prom=0;for(double ac:aopi)prom+=ac;
		// for(tmod ac:aopi)std::cout << ac << ' '; std::cout << std::endl;
		// for(tmod ac:normi)std::cout << ac << ' '; std::cout << std::endl;
		return {time,communication,mx_opi-mn_opi,prom/double(opinion.size())};
	}
};

std::function<std::vector<int>(const std::vector<double>&,const std::vector<Edge<double>>&,const double) >
DeGroot_selector=[](const std::vector<double>&opinion,const std::vector<Edge<double>>&edge,const double EPS)->std::vector<int>{
	std::vector<int> rs(edge.size());for(int i=0;i<int(rs.size());++i)rs[i]=i; return rs;
};

typedef Model<double,DeGroot_selector,bool(1)> Hybrid_DeGroot;
typedef Model<double,DeGroot_selector,bool(0)> Npupet_DeGroot;

std::function<std::vector<int>(const std::vector<double>&,const std::vector<Edge<double>>&,const double) >
S5_selector=[](const std::vector<double>&opinion,const std::vector<Edge<double>>&edge,const double EPS)->std::vector<int>{
	std::vector<int> rs;
	double prom=0;for(double o:opinion)prom+=o; prom/=double(opinion.size());
	// std::cout << prom << "?????" << std::endl;
	for(int i=0;i<int(edge.size());++i){
		// u -> v
		double ou=opinion[edge[i].u],ov=opinion[edge[i].v];
		// std::cout << ou << " ??? " << ov << std::endl;
		if( (ov>prom&&ov>ou) || (ov<prom&&ov<ou) )rs.push_back(i);
	} return rs;
};

typedef Model<double,S5_selector,bool(1)> Hybrid_S5;
typedef Model<double,S5_selector,bool(0)> Npupet_S5;

std::function<std::vector<int>(const std::vector<double>&,const std::vector<Edge<double>>&,const double) >
Wafle_selector=[](const std::vector<double>&opinion,const std::vector<Edge<double>>&edge,const double EPS)->std::vector<int>{
	std::vector<int> rs; double prom=0;for(double o:opinion)prom+=o; prom/=double(opinion.size());
	const int n=opinion.size(),m=edge.size();
	
	std::vector<std::vector<int>> inverse_graph(n);
	for(int i=0;i<m;++i)inverse_graph[edge[i].v].push_back(i);
	for(int nd=0;nd<n;++nd){
		// std::cout << n << " early start " << nd << std::endl;
		std::vector<int> &nedge=inverse_graph[nd]; std::vector<double>blck;
		
		for(int eind:nedge)blck.push_back((opinion[edge[eind].u]-opinion[nd])*edge[eind].w );
		double vl=opinion[nd],tt=0;for(double &ac:blck){
			if(ac<0.0){vl+=ac;ac=-ac;}tt+=ac;
		} vl=prom-vl;
		if(vl<=0||tt<=vl){ // I can just take all thats less and its not enough
			for(int eind:nedge){
				bool c1=opinion[edge[eind].u]<opinion[nd];
				if((tt<=vl||c1)&&(vl<=0||!c1))rs.push_back(eind);
			}
			continue;
		} // Now I just have to choose elements from an all positive bag
		// std::cout << vl << " __ _ _ _ __ " << nd << std::endl;
		const int h=nedge.size();
		// I have h+1 elements, want an answer |x-x*|<EPS ; so discretization on
		// block size K=EPS/h blocks ensures \phi:Double \to Integer
		// that \phi(x)-x <=K and h summands have error <=K*h=EPS LOLLOLOLOLOLOLXDXD
		// This idea is not new, its an FPTAS based on knapsack
		// ChatGPT references: * Vazirani – “Approximation Algorithms” (2001)
		// * Kellerer, Pferschy, Pisinger – Knapsack Problems (Springer, 2004)
		const double k=EPS/double(h);
		std::vector<int> ren(h);for(int i=0;i<h;++i)ren[i]=std::floor( blck[i]/k );
		const int obj=std::floor(vl/k);
		
		// std::cout << obj; for(int i=0;i<h;++i)std::cout << "| (" << ren[i] << ";"<<blck[i] << ") ";std::cout << std::endl;
		
		std::vector<int> knap(std::floor(1.0/k)+1,-1);knap[0]=-3333;
		const int skn=knap.size();
		
		// std::cout << skn << "??????"<<std::endl;
		
		for(int i=0;i<h;++i)for(int j=skn-ren[i]-1;j>=0;--j)if(knap[j+ren[i]]==-1&&knap[j]!=-1){
			assert(j+ren[i]<skn);
			knap[j+ren[i]]=i;
		}
		// std::cout << "xdxdxd"<<std::endl;
		int bstval=0;for(int i=0;i<skn;++i)if(knap[i]!=-1&&abs(obj-i)<=abs(obj-bstval))bstval=i;
		
		// std::cout << "adfa " << bstval << std::endl;
		std::vector<bool> us(h,0);
		while(bstval){
			// std::cout << knap[bstval] << "?"<<bstval<<std::endl;
			us[knap[bstval]]=1;
			
			bstval=bstval-ren[knap[bstval]];
		}
		// std::cout << "??ADFA " << std::endl;
		for(int i=0;i<h;++i){
			int eind =nedge[i];
			bool c1=opinion[edge[eind].u]<opinion[nd];
			if(c1^us[i])rs.push_back(eind);
		}
		double rval=opinion[nd];
		for(int i=0;i<h;++i)if(us[i]){
			auto e=edge[nedge[i]];
			rval+=(opinion[e.u]-opinion[nd])*e.w;
		}
		
		// std::cout << " ends " << nd << "__"<<rval<<"?"<<prom << std::endl;
	}
	/*std::sort(rs.begin(),rs.end());
	int prv=-1;for(int eind:rs){
		assert(prv!=eind);prv=eind;
	}*/
	return rs;
};

// Note this heuristic is not meant for the Hybrid model
typedef Model<double,Wafle_selector,bool(1)> Hybrid_Wafle;
typedef Model<double,Wafle_selector,bool(0)> Npupet_Wafle;

/*
std::function<std::vector<int>(const std::vector<double>&,const std::vector<Edge<double>>&,const double) >
BWafle_selector=[](const std::vector<double>&opinion,const std::vector<Edge<double>>&edge,const double EPS)->std::vector<int>{
	std::vector<int> rs; double prom=0;for(double o:opinion)prom+=o; prom/=double(opinion.size());
	const int n=opinion.size(),m=edge.size();
	
	std::vector<std::vector<int>> inverse_graph(n);
	for(int i=0;i<m;++i)inverse_graph[edge[i].v].push_back(i);
	for(int nd=0;nd<n;++nd){
		std::vector<std::vector<double>> side(2);
		const int indeg=inverse_graph[nd].size();
		const std::vector<int> bnd={0,indeg/2,indeg};
		for(int sd=0;sd<2;++sd){
			const int l=bnd[sd],r=bnd[sd+1];
			std::vector<double> &pos=side[sd],nx;
			pos={0};for(int i=l;i<r;++i){
				for(double &vl:pos)nx.push_back(vl+)
				std::swap(pos,nx);
			}
		}

	}
	return rs;
};


// This is the Brute-Wafle heuristic. Each subproblem is dealt in $O(\sum_i 2^{indeg(i)/2})$
typedef Model<double,BWafle_selector,bool(1)> Hybrid_BWafle;
typedef Model<double,BWafle_selector,bool(0)> Npupet_BWafle;*/
