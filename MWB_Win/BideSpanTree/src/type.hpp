#ifndef TYPE_H
#define TYPE_H

	#include <unordered_map>
	#include <unordered_set>
	#include <vector>
	#include <list>
	#include <set>
	#include <cstring>
	#include <map>
	#include <string>
	#include <cstdint>

	using namespace std;
	
	void Load_ini(void);
	
	typedef list< int > Itemset;
	typedef list < Itemset > SequentialPattern;
	
	struct Noeud
	{
		Noeud * fils;
		Noeud * frere;
		Itemset Value;
	};
	
	struct Arbre
	{
		Noeud * racine;
		int hauteur;
	};
	
	typedef pair<int, int> pair_int;
	typedef list <pair_int> SDB;
	typedef std::unordered_map<int, int> map_int;
	typedef std::unordered_set<int> set_int;
	typedef std::unordered_map<int, pair_int> map_int_pair;
	
	typedef pair<SDB::const_iterator, SDB::const_iterator> TOccurrence;	
	typedef pair<int, list<TOccurrence> > SeqPattern;

	typedef std::unordered_map<int,SeqPattern> ProjectedDB;
	typedef std::unordered_map<int,uint64_t> Sum_sequences;
	
	typedef pair<int, Arbre> PArbre;
	typedef std::unordered_map<uint64_t, PArbre > map_list_sum;
	typedef pair<int, list<SequentialPattern> > PListSeqP;
	typedef std::unordered_map<uint64_t, PListSeqP > map_list_pattern;


#endif //TYPE_H
