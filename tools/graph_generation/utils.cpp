#include "graph.cpp"
#include <set>

#pragma once

template<typename tpow> constexpr tpow mpow(tpow x, long long e, tpow m){
	tpow res=1;
	while(e){
		if(e&1ll)
			res = (res * 1ll *x)%m;
		e>>=1;
		x=(x*1ll*x)%m;
	}
	return res;
}

template<typename tedge>
std::vector<Edge<tedge>> remove_duplicate(const std::vector<Edge<tedge>>& edges){
	std::vector<Edge<tedge>> ans;
	std::set<std::pair<int, int>> is_exist;
	for(const Edge<tedge>&e : edges){
		std::pair<int, int> p(e.u, e.v); 
		if(e.u != e.v && !is_exist.count(p)){
			ans.push_back(e);
			is_exist.insert(p);
		}
	}
	return ans;
}