#ifndef FORWARD_H
#define FORWARD_H

	#include "type.hpp"
	#include <cstdio>
	
	void Forward_check
	(	
		SeqPattern &SeqPat,
		ProjectedDB &NewOccurrences,
		int depth,
		map_extension & extension_in, 
	  map_extension & extension_out
	);
	
	void support_count
	(
		int value,
		set_int &current_, 
		int &sup, 
		vector<int> & map_extension,
		int id_seq
	);
	
	void build_ProjectedBD
	(
		int support,
		bool itemset,
		SDB::const_iterator PosBegin, 
		SDB::const_iterator PosEnd,
		ProjectedDB &Size1Item
	);
	
#endif //FORWARD_H