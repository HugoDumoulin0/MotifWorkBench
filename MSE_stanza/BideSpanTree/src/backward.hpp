#ifndef BACKWARD_H
#define BACKWARD_H

	#include "type.hpp"

	int Backward_check
	(	
		int & hasBackwardExtention, 
		SeqPattern & SeqP,
		int &pruning,
		int depth
	);
	
	int support_prun_count
	(
		int value,
		set_int &current_occ,
		set_int &current_, 
		pair_int &occ_sup_prun, 
		int & hasBackwardExtention, 
		int & pruning, 
		int sup, 
		int cmpt, 
		list <TOccurrence >::const_iterator it_Occ, 
		list <TOccurrence >::const_iterator & End_it_Occ, 
		SDB::const_iterator it_SDB, 
		int End_itList
	);

#endif //BACKWARD_H