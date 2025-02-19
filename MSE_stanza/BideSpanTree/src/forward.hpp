#ifndef FORWARD_H
#define FORWARD_H

	#include "type.hpp"
	
	void Forward_check
	(	
		int & hasForwardExtention,
		SeqPattern &SeqPat,
		ProjectedDB &NewOccurrences,
		Sum_sequences &SSeq,
		int depth
	);
	
	void support_count
	(
		int value,
		set_int &current_, 
		int &occ_sup, 
		int & hasForwardExtention, 
		int sup,
		bool itemset,
		Sum_sequences &SSeq,
		int seq_id
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