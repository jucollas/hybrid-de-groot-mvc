/* Author: Oscar Vargas Pabon
This just defines the Edge structure. Notice that a graph may be represented
    as a vector/list of Edges.
*/
#pragma once
template <typename tedge> struct Edge{
	int u,v; tedge w;
	Edge()=default;
	Edge(int uu,int vv,const tedge &ww):u(uu),v(vv),w(ww){};
};