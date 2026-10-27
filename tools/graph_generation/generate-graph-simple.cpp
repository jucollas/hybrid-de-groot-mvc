#include <iostream>
#include <iomanip>
#include <cassert>
#include <fstream>

#include "gen.cpp"
#include "graph_metrics.cpp"
#include "utils.cpp"

typedef long long lint;

const int PREC = 8;
const int mod = 1e9;
const int EIN = 2, EOUT = 2, GIRTH = 3;
const int K = 1;
const std::string dir = "../../generated-graphs/";

int main(int argc, char* argv[]){
	const int N = argc > 1 ? std::stoi(argv[1]) : 10;
	const std::string name_out_file = argc > 2 ? argv[2] : "graph.txt"; 

	std::vector<Edge<double>> edge = gen_barabasiAlbert_scg(N, EIN, EOUT, GIRTH);
	std::vector<double> opi = gen_lv_opi(N, edge);

	assert(strongly_connected(N, edge));
	std::vector<Edge<double>> clean_edge = remove_duplicate(edge);

	std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

	std::ofstream outfile(dir + name_out_file);
	if(!outfile.is_open()){
		std::cerr << "Error : Could not open file " << name_out_file << std::endl;
		return 1;
	}
	outfile << std::setprecision(PREC) << std::fixed;
	outfile << N << ' ' << clean_edge.size() << '\n';
	for(int i = 0; i < N; ++i)
		outfile << i << " " << opi[i] << "\n";
	for(const Edge<double>&e : clean_edge) 
		outfile << e.u << ' ' << e.v << ' ' << e.w << '\n';	
	outfile.close();
	return 0;
}