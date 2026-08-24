/* Author: Oscar Vargas Pabon
Based loosely on the paper:

Fast unfolding of communities in large networks
Vincent D. Blondel1;a, Jean-Loup Guillaume1,2;b, Renaud
Lambiotte1,3;c and Etienne Lefebvre

This is an implementation of the directed louvain method. It calculates communities
	on the graph based on the directed modularity measure. The algorithm is greedy 
	by nature, so it doesnt calculate the optimal solution.  It doesnt have a provable complexity,
	yet expect it to work really fast.
The main function is 'di_louvain'. It takes as input the number of nodes and a vector of edges. 
	It returns a tree structure that represents the hierarchy of communities. 
	The leaves of the tree are the original nodes, and the internal nodes are the communities.
	Each internal node has as children the nodes that belong to that community.
FUNCTION 'di_louvain' DOESNT MANAGE LTree AFTER RETURN. THE USER MUST DELETE THE TREE AFTER USE.
*/

#pragma once

//#define TEST_LOUVAIN_MODE
#include"graph.cpp"
#include<vector>
#include<functional>
#include<map>

struct LTree{
	int node;
	std::vector<LTree*> child;
	LTree():node(-1) {};
	LTree(int nd):node(nd){};
	~LTree(){for(LTree*c:child)delete c;}
};
// Modularity:
// 1/(2m) \sum_{i,j}[c_i==c_j](A_{ij}-\frac{k_ik_j}{2m})
// where k_i=\sum_j A_{ij} ; c_i is the group of node i ; m is the amount of nodes
// delta modularity
// \frac{\sum_in+k_i}{2m}
template<typename tedge>
LTree* di_louvain(int n,std::vector<Edge<tedge>> edge){
	//for(auto e:edge)assert(e.w==0.); // was failing xd

	std::vector<std::vector<int>> e_adj(n);
	std::vector<tedge> k_in(n),k_out(n);
	std::vector<tedge> s_kin(n),s_kout(n);// sum on all elements of the class
	std::vector<int> c(n);
	auto init_gr=[&](){
		e_adj.resize(n);
		for(int i=0;i<n;++i)e_adj[i].clear();
		k_in.resize(n);k_out.resize(n);
		for(int i=0;i<n;++i)k_in[i]=k_out[i]=0;
		for( int i=0;i<int(edge.size());++i) {
			const Edge<tedge>&e=edge[i];
			e_adj[e.u].push_back(i);
			if(e.u!=e.v)e_adj[e.v].push_back(i);
		} for(int i=0;i<n;++i)for(int eind:e_adj[i]){
			k_in[edge[eind].v]+=edge[eind].w;
			k_out[i]+=edge[eind].w;
		} for(int i=0;i<n;++i)c[i]=i;
		s_kin.resize(n);s_kout.resize(n);
		for(int i=0;i<n;++i)s_kin[i]=k_in[i],s_kout[i]=k_out[i];
	}; 

	
	std::vector<LTree*> hier_cl(n);for(int i=0;i<n;++i)hier_cl[i]=new LTree(i);

	auto calc_modularity=[&]()->tedge{
		tedge res=0; // calculates in O(n+m) the modularity
		// Im overcounting all except self edges if I dont add the *2
		for(int i=0;i<n;++i)res-=(k_in[i]*s_kout[c[i]] + s_kin[c[i]]*k_out[i])/tedge(2*n);
		for(const Edge<tedge>&e:edge)if(c[e.u]==c[e.v]){
			res+=e.w;
		} return res;//tedge(2*n);
	};  // added
	// sum_i A_{i,nd}+A{nd,i} - \sum_i k_in[i]*k_out[nd]/m - \sum_i k_out[i]*k_in[nd]/m
	// saij - sk_in[cl]*k_out[nd]/m

	int chng=-1;while(chng!=0){ chng=0; init_gr();

		std::vector<bool> st_in(n,1),us(n,0);
		tedge a_modu=calc_modularity(); std::vector<tedge> ncl(n);
		std::vector<int> st(n);for(int i=0;i<n;++i)st[i]=i;

		//std::cerr << " gdafadf  this is ittttt "<<n << " ** " << st.size() << std::endl;
		while( !st.empty() ){
			const int nd=st.back();st.pop_back(); st_in[nd]=0;ncl[c[nd]]=0;
			//std::cerr << nd << " inicia este " << n << std::endl;
			
			
			std::vector<int> vcl;//NOTE this vector can be optimized a bit
			// by always keeping it with O(n) memory reserved
			for(int eind:e_adj[nd])if(edge[eind].u!=edge[eind].v){
				const Edge<tedge>&e=edge[eind]; //checking on all neighbors
				const int ot=(e.u==nd)?e.v:e.u,cl=c[ot];
				if(!us[cl])us[cl]=1,ncl[cl]=0,vcl.push_back(cl);
				ncl[cl]+=e.w;
				#ifdef TEST_LOUVAIN_MODE
					//std::cerr << e.w << " __ " << upd << '\n';
				#endif // TEST_LOUVAIN_MODE
			}
			const tedge cnst=ncl[c[nd]]-(k_in[nd]*(s_kout[c[nd]]-k_out[nd])+(s_kin[c[nd]]-k_in[nd])*k_out[nd])/tedge(n);
			//const tedge cnst=ncl[c[nd]]-(k_in[nd]*(s_kout[c[nd]]-0.)+(s_kin[c[nd]]-0.)*k_out[nd])/tedge(n);
			int b_cl=c[nd];tedge b_vl=0; for(int cl:vcl)if(cl!=c[nd]){
				tedge a_vl=ncl[cl]-(k_in[nd]*s_kout[cl]+ s_kin[cl]*k_out[nd])/tedge(n);
				a_vl-=cnst; //a_vl/=tedge(2*n);
				#ifdef TEST_LOUVAIN_MODE
					const double EPS=1e-8;
					double v1=s_kin[c[nd]],v2=s_kin[cl],v3=s_kout[c[nd]],v4=s_kout[cl];
					s_kin[c[nd]]-=k_in[nd];s_kout[c[nd]]-=k_out[nd];
					s_kin[cl]+=k_in[nd]; s_kout[cl]+=k_out[nd];
					int tmp=c[nd];c[nd]=cl; tedge xd=calc_modularity();c[nd]=tmp;
					s_kin[c[nd]]=v1;s_kout[c[nd]]=v3;
					s_kin[cl]=v2; s_kout[cl]=v4;
					tedge base=calc_modularity();
					std::cerr<<xd <<" _ _ _ " << a_modu+a_vl << " -> " << fabs((a_modu+a_vl)-xd) << std::endl;
					std::cerr << "base " << base << " a modu " << a_modu << " diff " << fabs(a_modu-base) << std::endl;
					std::cerr<< "differences xd " << xd-base << ' ' << a_vl << " -> " << fabs(xd-base-a_vl) << std::endl;
					assert(fabs((a_modu+a_vl)-xd)<=EPS);
				#endif // TEST_LOUVAIN_MODE

				if(a_vl>b_vl)b_vl=a_vl,b_cl=cl;
			}for(int cl:vcl)us[cl]=0;

			if(b_cl!=c[nd]){ ++chng;//updating stack
				s_kin[c[nd]]-=k_in[nd]; s_kout[c[nd]]-=k_out[nd];
				s_kin[b_cl] +=k_in[nd]; s_kout[b_cl] +=k_out[nd];
				for(int eind:e_adj[nd]){
					const Edge<tedge>&e=edge[eind];const int ot=(e.u==nd)?e.v:e.u;
					if(ot==nd||st_in[ot])continue;
					st_in[ot]=1;st.push_back(ot);
				} c[nd]=b_cl; a_modu+=b_vl;

			}
		} if(chng==0)continue;
		//std::cerr << "hca " << chng << std::endl;
		// renaming the color to range [1..k]
		std::map<int,int> ren;for(int i=0;i<n;++i)ren[c[i]]=-1;
		int k=0;for(auto&ac:ren)ac.second=k++;
		//std::cerr<<"ne comprende " << n << ' ' << k << std::endl;
		if(k>=n){chng=0;continue;}

		//std::cerr << "renaming" << std::endl;

		// building the new layer of the tree
		std::vector<int> cnt(k,0);for(int i=0;i<n;++i)++cnt[ren[c[i]]];
		std::vector<LTree*> n_hier_cl(k,NULL);for(int i=0;i<n;++i){
			const int cind=ren[c[i]];
			if(cnt[cind]==1)n_hier_cl[cind]=hier_cl[i];
			else{ if(!n_hier_cl[cind])n_hier_cl[cind]=new LTree;
				n_hier_cl[cind]->child.push_back(hier_cl[i]);
			}
		} std::swap(hier_cl,n_hier_cl);

		//std::cerr << "n_lay____renaming" << std::endl;

		// updating edges and edge weights
		std::vector<Edge<tedge>> nedge; std::map<std::pair<int,int>,int> iedge;
		for(const Edge<tedge> &e:edge){
			const int nu=ren[c[e.u]],nv=ren[c[e.v]];
			if(!iedge.count({nu,nv})){iedge[{nu,nv}]=nedge.size();nedge.emplace_back(nu,nv,0);}
			nedge[iedge[{nu,nv}]].w+=e.w;
		} std::swap(edge,nedge);
		n=k;
		//std::cerr << "ndiadñfjad " << std::endl;
	}  LTree*res;if(n==1)res=hier_cl.front();
	else res=new LTree,res->child=hier_cl;
	return res;
}