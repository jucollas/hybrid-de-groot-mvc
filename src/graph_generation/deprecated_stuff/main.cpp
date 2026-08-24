/*
Author: Oscar vargas pabon

Hybrid_DeGroot TESTED with peñas old stuff
Hybrid_S5      TESTED with peñas old stuff

Notes:
The edge-selector of Wafles works in time
per node:  O(h/EPS*h)
Total   :  O(\sum h_i^2/EPS) which is, apparently, bounded by O(VE/EPS)

*/
#include"model.cpp"
#include"parsing.cpp"
#include "graph_metrics.cpp"
#include "gen.cpp"

#include<string>

#include <chrono>
auto take_time=[](){return std::chrono::high_resolution_clock::now();};
auto get_durat=[](auto start){ return std::chrono::duration_cast<std::chrono::milliseconds>(take_time() - start).count(); };

void read_stdin(double EPS){
	auto state=read_state();
	while(!state.first.empty()){
		// Hybrid_DeGroot
		Npupet_DeGroot
		m1(state.first,state.second);
		// Hybrid_S5
		Npupet_S5
		m2(state.first,state.second);
		// Hybrid_Wafle
		Npupet_Wafle
		m3(state.first,state.second);
		// for(double ac:state.first )std::cout << ac << ' ' ; std::cout << std::endl;
		
		// break;
		auto rs=m1.sim(EPS);
		std::cout << '\n';
		std::cout << "nodes "<< state.first.size() << " edges " << state.second.size() << '\n';
		std::cout << " algo     time        communication\n";
		std::cout << " degroot "<< std::get<0>(rs) << ' ' << std::get<1>(rs) << std::endl;
		rs=m2.sim(EPS);
		std::cout << " s5      "<< std::get<0>(rs) << ' ' << std::get<1>(rs) << std::endl;
		rs=m3.sim(EPS);
		std::cout << " wafle   "<< std::get<0>(rs) << ' ' << std::get<1>(rs) << std::endl;
		
		// break;
		
		state=read_state();
	}
}

std::vector<Edge<double>> gen_test(const int n,int ein,int eout,int girth=3){
	std::vector<Edge<double>> edg=gen_barabasiAlbert_scg(n,ein,eout,girth);
	int diameter=-1,radius=-1;
	if(n*1ll*n<=int(1e8)*1ll)
		std::tie(diameter,radius)=graph_metrics<double>(n,edg);
	std::cout << "Diameter " << diameter << " _Radius " << radius << '\n';
	std::cout << "Total_edges_(with_self-edges) " << edg.size() << " _Mean " << double(edg.size())/double(n) << '\n';
	assert(diameter<=n);
	return edg;
}

void use_gen(int iter,int n,double EPS){
	//std::cout << (n*(n-1))/2+n << "?????????"<<std::endl;
	std::cout << "Seeeeed " << seed << " Case_amount " << iter 
				<< " graph_size " << n << " Epsilon " << EPS  << '\n';
	for(int it=0;it<iter;++it){
		std::cout << "\nCase " << it << '\n';
		std::vector<double> opi=gen_opi(n);

		////                                  n,ein,eout,girth
		std::vector<Edge<double>> edg=gen_test(n,10,1,10);
		//std::vector<Edge<double>> edg=gen_barAlb_trans(n);
		double mx_opi=-1,mn_opi=2;for(double ac:opi)
			mx_opi=std::max<double>(mx_opi,ac),mn_opi=std::min<double>(mn_opi,ac);
		double bdelta=mx_opi-mn_opi;

		assert(strongly_connected(n,edg));
		
		Npupet_DeGroot m1(opi,edg);
		Npupet_S5      m2(opi,edg);
		Npupet_Wafle   m3(opi,edg);

		//std::cerr << "begins de groot" << std::endl;
		auto tin=take_time();

		int t1,c1;double d1,o1;
		std::tie(t1,c1,d1,o1)=m1.sim(EPS);
		auto rt1=get_durat(tin);
		//std::cerr << "ends de groot " << rt1 << std::endl;
		tin=take_time();
		int t2,c2;double d2,o2;
		std::tie(t2,c2,d2,o2)=m2.sim(EPS);
		auto rt2=get_durat(tin);
		//std::cerr << "ends de s5 " << rt2 << std::endl;
		tin=take_time();
		int t3,c3;double d3,o3;
		std::tie(t3,c3,d3,o3)=m3.sim(EPS);
		auto rt3=get_durat(tin);
		std::cout << " Name   |   Time(steps)  | Communications | runtime(miliseconds) | max-min | diff-change | opinion \n";
		std::cout << "DeGroot  " << t1 << "      " << c1 << "     " << rt1 << "    " << d1 << "    " << bdelta-d1 << "  " << o1 << '\n';
		std::cout << "S5       " << t2 << "      " << c2 << "     " << rt2 << "    " << d2 << "    " << bdelta-d2 << "  " << o2 << '\n';
		std::cout << "wafle    " << t3 << "      " << c3 << "     " << rt3 << "    " << d3 << "    " << bdelta-d3 << "  " << o3 << '\n';
	}
}

void megadeth(const std::string opi_gen="Uniform"){
	std::ios::sync_with_stdio(false);

	const int iter=100,girth=10,outdeg=1;
	const double eps=5e-2;
	const std::vector<int> indeg={2,4,6,10};
	const std::vector<int> n_sz={int(1e2),int(1e3),int(1e4),int(1e5)};

	//const std::vector<int> n_sz={int(5e1),int(1e2)};

	std::cout << iter << ' ' << girth << ' ' << outdeg << ' ' << eps << ' '
			<< indeg.size() << ' ' << n_sz.size() << ' ' << seed << '\n';
	for(int ac:indeg)std::cout << ac << ' ';
	std::cout << '\n';
	for(int ac:n_sz) std::cout << ac << ' ';
	std::cout << '\n';
	//// end of the metadata of deth
	for(int idg:indeg)for(int n:n_sz){
		std::cerr << "xdxdxd "<<idg << " _ " << n << std::endl;

		std::vector<int> diam(iter);

		std::vector<int> dg_stp(iter),dg_com(iter);
		std::vector<long long> dg_rtm(iter); 
		std::vector<double> dg_mxn(iter),dg_dlt(iter),dg_opi(iter);
		
		std::vector<int> s5_stp(iter),s5_com(iter);
		std::vector<long long> s5_rtm(iter);
		std::vector<double> s5_mxn(iter),s5_dlt(iter),s5_opi(iter);

		std::vector<int> wf_stp(iter),wf_com(iter);
		std::vector<long long> wf_rtm(iter);
		std::vector<double> wf_mxn(iter),wf_dlt(iter),wf_opi(iter);

		for(int i=0;i<iter;++i){
			std::vector<Edge<double>> edg=gen_barabasiAlbert_scg(n,idg,outdeg,girth);
			std::vector<double> opi;
			if(opi_gen=="Uniform")opi=gen_opi(n);
			else if(opi_gen=="Louvain")opi=gen_lv_opi(n,edg);
			else assert(0);

			double mx_opi=-1,mn_opi=2;for(double ac:opi)
				mx_opi=std::max<double>(mx_opi,ac),mn_opi=std::min<double>(mn_opi,ac);
			double o_delta=mx_opi-mn_opi;

			diam[i]=n*1ll*n<=int(1e7)*1ll?graph_metrics(n,edg).first:-1;

			Npupet_DeGroot mdg(opi,edg);
			Npupet_S5      ms5(opi,edg);
			Npupet_Wafle   mwf(opi,edg);

			auto tin=take_time();
			std::tie(dg_stp[i],dg_com[i],dg_mxn[i],dg_opi[i])=mdg.sim(eps);
			auto rt1=get_durat(tin);
			//std::cerr << "ends de groot " << rt1 << std::endl;
			tin=take_time();
			std::tie(s5_stp[i],s5_com[i],s5_mxn[i],s5_opi[i])=ms5.sim(eps);
			auto rt2=get_durat(tin);
			//std::cerr << "ends de s5 " << rt2 << std::endl;
			tin=take_time();
			
			std::tie(wf_stp[i],wf_com[i],wf_mxn[i],wf_opi[i])=mwf.sim(eps);
			auto rt3=get_durat(tin);
			
			dg_rtm[i]=rt1; s5_rtm[i]=rt2; wf_rtm[i]=rt3;
			dg_dlt[i]=o_delta-dg_mxn[i]; s5_dlt[i]=o_delta-s5_mxn[i]; wf_dlt[i]=o_delta-wf_mxn[i];

		}

		/// print stuff
		std::cout << '\n';
		for(int ac:diam)std::cout << ac << ' ';
		std::cout << '\n';

		for(int ac:dg_stp)std::cout << ac << ' ';
		std::cout << '\n';
		for(int ac:dg_com)std::cout << ac << ' ';
		std::cout << '\n';
		for(long long ac:dg_rtm)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:dg_mxn)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:dg_dlt)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:dg_opi)std::cout << ac << ' ';
		std::cout << '\n';

		for(int ac:s5_stp)std::cout << ac << ' ';
		std::cout << '\n';
		for(int ac:s5_com)std::cout << ac << ' ';
		std::cout << '\n';
		for(long long ac:s5_rtm)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:s5_mxn)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:s5_dlt)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:s5_opi)std::cout << ac << ' ';
		std::cout << '\n';

		for(int ac:wf_stp)std::cout << ac << ' ';
		std::cout << '\n';
		for(int ac:wf_com)std::cout << ac << ' ';
		std::cout << '\n';
		for(long long ac:wf_rtm)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:wf_mxn)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:wf_dlt)std::cout << ac << ' ';
		std::cout << '\n';
		for(double ac:wf_opi)std::cout << ac << ' ';
		std::cout << '\n';
	}
}

int main(int argc,char * argv[] ){
	std::cout << std::setprecision(12) << std::fixed;
	const double eps=0.005;

	if (argc>2&&std::string(argv[1])=="-sd"){
		seed=0;int ind=0;while(argv[2][ind]!='\0'){
			seed=seed*10ll+ argv[2][ind]-'0';
			++ind;
		} rng=std::mt19937(seed);
	}

	//gen_test();
	//use_gen(5,1e4,eps);
	//read_stdin(eps);

	megadeth("Uniform");
	//megadeth("Louvain");

	return 0;
}
