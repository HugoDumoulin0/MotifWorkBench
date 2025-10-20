#ifndef TYPE_H
#define TYPE_H

	#include <vector>
	#include <list>
	#include <map>
	#include <set>
	#include <cstring>
	#include <stdlib.h>

	using namespace std;
	
	void Load_ini(void);
	
	typedef unsigned int uint;
	typedef pair<int, int> pair_int;
	typedef list <pair_int> SDB;
	typedef map<int, int> map_int;
	typedef map<int, vector<int> > map_extension;
	typedef set<int> set_int;
	typedef map<int, pair_int> map_int_pair;
	
	typedef pair<SDB::const_iterator, SDB::const_iterator> TOccurrence;	
	typedef pair<int, list<TOccurrence> > SeqPattern;

	typedef map<int,SeqPattern> ProjectedDB;
	typedef map<int,uint> Sum_sequences;


#endif //TYPE_H