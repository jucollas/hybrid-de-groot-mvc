#include"gen.cpp"
#include"graph_metrics.cpp"
#include<iostream>
#include<iomanip>
#include<cassert>
typedef long long lint;
template<typename tpow> constexpr tpow mpow(tpow x,lint e,tpow m){tpow res=1;while(e){if(e&1ll)res=(res*1ll*x)%m;e>>=1;x=(x*1ll*x)%m;}return res;}
int main(){
	std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);
	std::cout << std::setprecision(16) << std::fixed;

	const int i_n=20,ein=2,eout=1,girth=3; 
	std::vector<Edge<double>> iedge=gen_barabasiAlbert_scg(i_n,ein,eout,girth);
	const int k=1,n=mpow<int>(i_n,k,int(1e9));
	std::vector<Edge<double>> edge=kronecker_up<double>(i_n,k,iedge);
	std::cerr << "xdxdxd " << n << " _ " << iedge.size() << " " << edge.size() << '\n';std::cerr.flush();
	std::vector<double> opi=gen_lv_opi(n,edge);
	std::cerr << " gets out and sees the world" << std::endl;

	std::cout << n << ' ' << edge.size() << '\n';
	for(int i=0;i<n;++i)std::cout << opi[i] << " \n"[i+1==n];
	for(const Edge<double>&e:edge)std::cout<< e.u << ' ' << e.v << ' ' << e.w << '\n';
	assert(strongly_connected(n,edge));
	return 0;
}