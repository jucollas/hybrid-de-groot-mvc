/*
Author:Oscar Vargas Pabon

Read on format
< nodes : <0:o_0>,..<k:o_k> > ; < edges : < (u_0,v_0) : I_{u_0v_0} >, .. <(u_k,v_k): I_{u_kv_k}> >

This is the format used in the /test folder
*/
#pragma once
#include<bits/stdc++.h>

#include"model.cpp"

char next_nonempty(){
	char t=getc(stdin);
	while( t==' '||t=='	'|| t== '\n' ) t=getc(stdin);
	return t;
}

std::pair<std::vector<double>,std::vector<Edge<double>>> read_state(){
	// std::cout << std::setprecision(12) << std::fixed;
	auto rmv=[](char srch){char t; do t=next_nonempty(); while( t != srch && t!=EOF ); return t;};
	auto rin=[](){
		int nd=0;char t=next_nonempty();
		while(t<'0'||t>'9')t=next_nonempty();
		while('0'<=t&&t<='9')nd=nd*10+t-'0',t=next_nonempty();
		return nd;
	};
	auto rfl=[](){
		double rs=0;char t=next_nonempty();
		while(t<'0'||t>'9')t=next_nonempty();
		while('0'<=t&&t<='9')rs=rs*10+t-'0',t=next_nonempty();
		if(t=='.'){
			double scale=0.1; t=next_nonempty();
			while('0'<=t&&t<='9')rs+=(t-'0')*scale,t=next_nonempty(),scale*=0.1;
			if(t=='e'){
				t=next_nonempty();
				int e=0;bool sgn=t=='-';
				if(sgn)t=next_nonempty();
				while('0'<=t&&t<='9')e=e*10+t-'0',t=next_nonempty();
				if(sgn)for(int i=0;i<e;++i)rs*=0.1;
				else for(int i=0;i<e;++i)rs*=10;
			}
		}
		return rs;
	};
	char t=rmv('<');
	if(t==EOF)return {{},{}};//no more file
	
	std::vector<double> opi;rmv(':');
	
	t=next_nonempty();
	while(t=='<'){
		int nd =rin();
		opi.resize(nd+1,-1);
		opi[nd]=rfl();
		
		t=next_nonempty();
		if(t==',')t=next_nonempty();
	}
	std::vector<Edge<double>>edge; rmv(':');
	t=next_nonempty();
	while(t=='<'){
		int u=rin(),v=rin(); double w=rfl();
		// if(!(u>=0&&v>=0&& w>=0.0 && w<=1.0))std::cout << u << " _ " << v << " ____ " << w << std::endl;
		// assert(u>=0&&v>=0&& w>=0.0 && w<=1.0);
		edge.emplace_back(u,v,w);
		
		t=next_nonempty();
		if(t==',')t=next_nonempty();
	}
	
	// Notes: the edges may not be normalized
	// * Peñas graphs may not have self-edges
	const int n=opi.size();
	std::vector<double> normi(n,0);
	for(const Edge<double> &e:edge)normi[e.v]+=e.w;
	for(Edge<double> &e:edge)e.w/=normi[e.v];
	// for(int i=0;i<n;++i)std::cout << i << " -> " << normi[i]<< std::endl;
	
	return {opi,edge};
}
