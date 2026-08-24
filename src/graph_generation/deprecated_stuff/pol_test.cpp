/*
Author: Oscar Vargas Pabon
*/
#include"model.cpp"
#include"pol_measures.cpp"
#include"gen.cpp"
#include<iostream>

void run_test(int graph_iter,int n,int indeg,int iter){
    const int girth=10,outdeg=1;
    std::cout << graph_iter << " " << n << " " << girth << " " << indeg << " " << outdeg << " " << iter << " " << seed << std::endl;
    const double c=1e-3;
    for(int i=0;i<graph_iter;++i){
        std::vector<Edge<double>> edg=gen_barabasiAlbert_scg(n,indeg,outdeg,girth);
        //std::vector<double> opi=gen_lv_opi(n,edg);
        std::vector<double> opi=gen_opi(n);
        std::vector<std::vector<double>> sim=Npupet_DeGroot(opi,edg).sim_opi(iter);
        for(int j=0;j<iter;++j){
            double mec=opi_MEC(sim[j],c);
            std::cout << mec << " \n"[j+1==iter];
        } for (int j=0;j<iter;++j){
            double er=opi_ER(sim[j],c);
            std::cout << er << " \n"[j+1==iter];
        } for (int j=0;j<iter;++j){
            double rge=range(sim[j]);
            std::cout << rge << " \n"[j+1==iter];
        }
    }
}

int main(){
    //pol_test();return 0;
    run_test(100,100,5,50);
    std::cerr<<"Ended and working with seed <" << seed << ">" << std::endl;
    return  0;
}