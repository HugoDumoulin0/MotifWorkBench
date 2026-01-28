#include "backward.hpp"

extern SDB New_SDB;
extern int _gap_min;
extern int _gap_max;
extern int _nb_itemset_max;
extern int _nb_itemset_min;

int Backward_check(int & hasBackwardExtention, SeqPattern & SeqP, int &pruning,int depth)
{
	set_int current_item;
	set_int current_itemset;
	set_int current_item_prun;
	set_int current_itemset_prun;
	map_int_pair occ_sup_in_prun;
	map_int_pair occ_sup_prun;
	list <TOccurrence >::const_iterator it_Occ(SeqP.second.begin()) , End_it_Occ(SeqP.second.end());
	int cmpt = 0;
// 	SDB::const_iterator pSequence(__null);
	int prec_id_seq;
	int posistion = 0;
	
	for (;it_Occ!=End_it_Occ;++it_Occ)
	{ // liste des occurrences par séquences
		++cmpt;
		SDB::const_iterator it_SDB(it_Occ->first) ;
		int id_seq = (*it_SDB).second;
		

		if (cmpt > 1) // si nous ne sommes pas dans la première occurrence
		{
			if (prec_id_seq != id_seq) //changement de séquence, on réinitialise les hash
			{
				current_itemset.clear();
				current_item.clear();
			}
		}
		prec_id_seq = id_seq;
		
		// Backward_check_in
		while((*--it_SDB).first != -1 && (*it_SDB).first != -2)
		{
			if ((*it_SDB).first > 0)
			{
				if (support_prun_count((*it_SDB).first, current_itemset_prun, current_itemset, occ_sup_in_prun[(*it_SDB).first], hasBackwardExtention, pruning, SeqP.first, cmpt, it_Occ, End_it_Occ, it_SDB, -1))
				{
					return 1;
				}
			}
		}
		// Backward_check_out
		if ( (*it_SDB).first != -2  && depth < _nb_itemset_max && depth >= _nb_itemset_min) // si on ne c'est pas arreté sur un changement de séquence
		{ 
			posistion = 0;
			while((*--it_SDB).first != -2)
			{
				if (posistion <= _gap_max)
				{
					if (posistion >= _gap_min)
					{
						if ((*it_SDB).first > 0)
						{
							if (support_prun_count((*it_SDB).first, current_item_prun, current_item, occ_sup_prun[(*it_SDB).first], hasBackwardExtention, pruning, SeqP.first, cmpt, it_Occ, End_it_Occ, it_SDB, -2))
							{
								return 1;
							}
						}
					}
					if ((*it_SDB).first == -1)
						++posistion;
				}
				else
					break;
			}
		}
		current_item_prun.clear();
		current_itemset_prun.clear();
	}
	return 0;
}

int support_prun_count(int value,
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
		       int End_itList)
{

	++it_Occ;
	if (current_occ.find(value) == current_occ.end())
	{
		++occ_sup_prun.first;		
		if (it_Occ == End_it_Occ) // dernière occurrence ?
		{
			if (occ_sup_prun.first == cmpt)
			{
				pruning = 1;
				return 1;
			}
		}
		current_occ.insert(value);
	}
	if (current_.find(value) == current_.end())
	{
		if (++occ_sup_prun.second == sup)
		{
			hasBackwardExtention = 1;
		}
		if (it_Occ == End_it_Occ) // dernière occurrence ?
		{ 
			if ((*it_SDB).first <= End_itList)
			{
				if (hasBackwardExtention)
					return 1;
			}
			++it_SDB;
		}
		current_.insert(value);
	}
	return 0;
}