#ifndef MAIN_H
#define MAIN_H

	#include "type.hpp"
	
	SDB Load_SDB
	(
		string & Corpus_to, 
		map_int & support_lenght1,
		map_extension & extension
	);
	
	void support_count
	(
		int, 
		set_int &current_,
		map_int &sup_,
		vector<int> & extension, 
		int seq_id
	);
	
	SDB Prun_no_freq
	(
		map_int & length1_support_SDB_new, 
		ProjectedDB & Size1Item
	);
	
	int PGrowth
	(
		string Prefix,
		SeqPattern & SeqPat,
		vector <bool> & _orbool, 
		vector <bool > &_inbool,
		int depth,
		bool appartenance_in,
		int next,
		vector<int> & extension
	);


#endif //MAIN_H