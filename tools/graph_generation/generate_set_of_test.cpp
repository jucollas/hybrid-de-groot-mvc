#include <iostream>
#include <iomanip>
#include <cassert>
#include <fstream>
#include <filesystem>
#include <string>

#include "gen.cpp"
#include "graph_metrics.cpp"
#include "utils.cpp"

typedef long long lint;

namespace fs = std::filesystem;

const int PREC = 8;
const int mod = 1e9;
const int EIN = 2, EOUT = 1, GIRTH = 3;
const int K = 1;
const int MIN_EDGE = 0.001;
const std::string dir = "../../data/generated-graphs/";

int main(int argc, char* argv[]){
	const int N_min = argc > 1 ? std::stoi(argv[1]) : 10;
	const int N_max = argc > 2 ? std::stoi(argv[2]) : 100;
	const int step = argc > 3 ? std::stoi(argv[3]) : 10;
	const std::string folder_name = argc > 4 ? std::string(argv[4]) + "/" : "set_test_02/";

	fs::path dir_path(dir  + folder_name);
	if(!(fs::exists(dir_path) && fs::is_directory(dir_path))){
		fs::create_directory(dir + folder_name);
	}

	for(int n = N_min; n < N_max; n += step){
		std::vector<Edge<double>> edge = gen_barabasiAlbert_scg(n, EIN, EOUT, GIRTH);
		//cout << max_indegre
		//std::vector<Edge<double>> clean_edge = remove_duplicate(edge);
		gen_edges_with_minima(n, edge, 0.5);

		std::vector<double> opi = gen_lv_opi(n, edge);
		
		assert(strongly_connected(n, edge));

		std::ios_base::sync_with_stdio(false);
    	std::cin.tie(NULL);

    std::string name_out_file = "test_" + std::to_string(n) + ".txt";

		std::ofstream outfile(dir + folder_name  + name_out_file);
		if(!outfile.is_open()){
			std::cerr << "Error : Could not open file " << name_out_file << std::endl;
			return 1;
		}
		outfile << std::setprecision(PREC) << std::fixed;
		outfile << n << " " << (int) edge.size() << "\n";
		for(int i = 0; i < (int) opi.size(); ++i)
			outfile << i << " " << opi[i] << "\n";
		for(const Edge<double>&e : edge)
			outfile << e.u << " " << e.v << " " << e.w << "\n";
		outfile.close();
	}
	return 0;
}