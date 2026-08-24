/*
Author:Oscar Vargas Pabon
*/
#pragma once
#include<vector>
#include<cmath>
#include<algorithm>

std::pair<std::vector<double>,std::vector<double>> discretize_opi(const std::vector<double>&raw_opinion,double c=1e-2){
    std::vector<double>pi,x;
    std::vector<double> opi=raw_opinion; std::sort(opi.begin(),opi.end());
    double prev=-1; for(double ac:opi){
        if(ac-prev>c) {
            prev=ac;pi.push_back(1); x.push_back(ac);
        } else ++pi.back();
    } return {pi,x}; }
double dEC(const std::vector<double>&pi,const std::vector<double>&x,double alpha,double beta,double y){
    const int n=pi.size();
    double res=0;for(int i=0;i<n;++i){
        const double inc=pow(pi[i],alpha)*beta*pow(fabs(x[i]-y),beta-1);
        if(x[i]<=y)res+=inc; else res-=inc;
    } return res; }
double EC(const std::vector<double>&pi,const std::vector<double>&x,double alpha,double beta,double y){
    const int n=pi.size();
    double res=0;for(int i=0;i<n;++i)res+=pow(pi[i],alpha)*pow(fabs(x[i]-y),beta);
    return res; }
double argminEC(const std::vector<double>&pi,const std::vector<double>&x,double alpha=2,double beta=1.15){
    double l=0,r=1;for(int i=0;i<50;++i){
        double m=(l+r)/2;
        if(dEC(pi,x,alpha,beta,m)<.0)l=m; else r=m;
    } return (l+r)/2; }
double MEC(const std::vector<double>&pi,const std::vector<double>&x,double alpha=2,double beta=1.15){
    return EC(pi,x,alpha,beta,argminEC(pi,x,alpha,beta)); }
double opi_MEC(const std::vector<double>&opinion,double c=1e-2,double alpha=2,double beta=1.15){
    std::vector<double>pi,x;std::tie(pi,x)=discretize_opi(opinion,c);
    return MEC(pi,x,alpha,beta); }
double ER(const std::vector<double>&pi,const std::vector<double>&x,double alpha=1.6,double K=1/(2*pow(0.5,2+1.6))){
    const int n=pi.size();
    double res=0;for(int i=0;i<n;++i)for(int j=0;j<n;++j)
        res+=pow(pi[i],1+alpha)*pi[j]*fabs(x[i]-x[j]);
    return res*=K; }
double opi_ER(const std::vector<double>&opinion,double c=1e-2,double alpha=1.6,double K=1/(2*pow(0.5,2+1.6))){
    std::vector<double>pi,x;std::tie(pi,x)=discretize_opi(opinion,c);
    return ER(pi,x,alpha,K); }
double range(const std::vector<double>&opinion){
    double mn=2,mx=-1;for(double ac:opinion)mn=std::min(mn,ac),mx=std::max(mx,ac);
    return mx-mn; }

void pol_test(){
    std::vector<double> x={0.2};
    std::vector<double> pi={100};
    std::cerr << "MEC " << MEC(pi,x) << " y* " << argminEC(pi,x) << std::endl;
    std::cerr << "ER " << ER(pi,x) << std::endl;
    x={0,1};
    pi={100,100};
    std::cerr << "MEC " << MEC(pi,x) << " y* " << argminEC(pi,x) << std::endl;
    std::cerr << "ER " << ER(pi,x) << std::endl;
}
