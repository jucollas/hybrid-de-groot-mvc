/*Author: Oscar Vargas Pabon
Tests for some elements generated in gen.cpp
*/
#include"gen.cpp"
#include<iostream>
#include<future>
#include<cassert>
#include<set>
bool test_edge_weight(int iter,int n,double minima,bool out=false){
	assert( double(n)<=1./minima );
	for(int tm=0;tm<iter;++tm){if(out&&tm%10==0)std::cerr << "Time " << tm << " - " << n << " _ " << minima << std::endl;
		std::vector<Edge<double>> edges=gen_scg(n,0.45);
		gen_edges_with_minima(n,edges,minima);
		double min_edge=2;for(auto&e:edges)min_edge=std::min<double>(min_edge,e.w);
		if(!(minima==0. || min_edge==minima))return 0;
		std::vector<double> sm(n,0.);
		for(auto&e:edges)sm[e.v]+=e.w;
		for(int i=0;i<n;++i)if(!(sm[i]<=1.))return 0;
		for(auto&e:edges)if(!(e.w>0))return 0;
	}if(out)std::cerr << "termino todo bien" << std::endl;
	return 1;
}void all_test_edge_weight(){
	const bool out=0;
	std::cerr << "Start testing edge-weight generation" << std::endl;
	std::future<bool> v1=std::async(std::launch::async,test_edge_weight,100,1000,0.001,out);
	std::future<bool> v2=std::async(std::launch::async,test_edge_weight,1000,100,0.01,out);
	std::future<bool> v3=std::async(std::launch::async,test_edge_weight,3,10000,1./double(10000*2),out);
	std::future<bool> v4=std::async(std::launch::async,test_edge_weight,100,100,0,out);
	assert(v1.get()&&v2.get()&&v3.get()&&v4.get());
	std::cerr << "Finishes testing edge weight generation" << std::endl;
}bool test_barabasi_albert(int iter,int n,int ein,int eout,int girth,bool out=0){
	// const int iter=1000;
	// const int n=1000,ein=4,eout=5,girth=3;
	for(int tm=0;tm<iter;++tm){ if(out&&tm%10==0)std::cerr << "time: " << tm << std::endl;
		std::vector<Edge<double>> edges=gen_barabasiAlbert_scg(n,ein,eout,girth);
		//for(auto&e:edges)std::cerr << e.u << " " << e.v << " " << e.w << std::endl;
		std::set<std::pair<int,int>> edg;for(auto&e:edges){
			if(edg.count({e.u,e.v}))return 0;
			edg.insert({e.u,e.v});
		}
	}if(out)std::cerr << "todo etdmrinña bien " << std::endl;
	return 1;
}void all_test_barabasi_albert(){
	const bool out=0;
	std::cerr << "Start testing barabasi albert" << std::endl;
	std::future<bool> v1=std::async(std::launch::async,test_barabasi_albert,1000,1000,4,5,3,out);
	std::future<bool> v2=std::async(std::launch::async,test_barabasi_albert,100,10000,10,10,50,out);
	std::future<bool> v3=std::async(std::launch::async,test_barabasi_albert,1000,100,2,1,2,out);
	assert(v1.get()&&v2.get()&&v3.get());
	std::cerr << "Finished testing barabasi albert" << std::endl;

} int main(){
	all_test_edge_weight();
	all_test_barabasi_albert();
	return 0;
}