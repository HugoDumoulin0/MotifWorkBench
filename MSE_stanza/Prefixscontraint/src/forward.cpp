#include "forward.hpp"

extern SDB New_SDB;

extern int _supmin;
extern int _gap_min;
extern int _gap_max;
extern int _nb_itemset_max;

void Forward_check(SeqPattern &SeqP, ProjectedDB &NewOccurrences, int depth, map_extension & extension_in, map_extension & extension_out)
{
	set_int current_item;
	set_int current_itemset;
	map_int occ_sup_in;
	map_int occ_sup_out;
	list <TOccurrence >::const_iterator it_Occ(SeqP.second.begin()) , End_it_Occ(SeqP.second.end());
	int prec_id_seq;
	bool iter = false;
	int posistion = 0;
	SDB::const_iterator NextEndPattern;
	
	// pass1
	for (;it_Occ!=End_it_Occ;++it_Occ)
	{
		SDB::const_iterator it_SDB(it_Occ->second) ;
		bool Next(false);
		NextEndPattern = (*++it_Occ).second;
		--it_Occ;
		
		int id_seq = (*it_SDB).second;
		
		if (iter) // si le pointeur pSequence n'est pas nul
		{
			if (prec_id_seq != id_seq) //changement de séquence, on réinitialise les hash
			{
				current_itemset.clear();
				current_item.clear();
			}
		}
		prec_id_seq = id_seq;
		iter = true;
		
		// Forward_check_in
		while((*++it_SDB).first != -1 && (*it_SDB).first != -2)
		{
			if ((*it_SDB).first > 0)
			{
				support_count((*it_SDB).first, current_itemset, occ_sup_in[(*it_SDB).first], extension_in[(*it_SDB).first], id_seq);
// 				fprintf(stderr, "item %i, seq %i\n", (*it_SDB).first, id_seq);
			}
		}
		// Forward_check_out
		if ( (*it_SDB).first != -2 && depth < _nb_itemset_max) // si on ne s'est pas arreté sur un changement de séquence
		{ 
			posistion = 0;
			while((*++it_SDB).first != -2)
			{
				if (NextEndPattern == it_SDB)
				{
					Next = true;
				}
				if (posistion <= _gap_max)
				{
					if (posistion >= _gap_min)
					{
						if ((*it_SDB).first > 0)
						{
							support_count((*it_SDB).first, current_item, occ_sup_out[(*it_SDB).first], extension_out[(*it_SDB).first], id_seq);
// 							fprintf(stderr, "item %i, seq %i\n", (*it_SDB).first, id_seq);
						}
					}
					if ((*it_SDB).first == -1)
					{
						++posistion;
						if (_gap_min == 0) // si pas de gap min, on peut traiter par séquence
						{
							if (Next)
							{
								break;
							}
						}
					}
				}
				else
				{
					break;
				}
			}
		}
	}
	
	// pass2
	it_Occ = SeqP.second.begin();
	for (;it_Occ!=End_it_Occ;++it_Occ)
	{
		SDB::const_iterator it_SDB(it_Occ->second) ;
		bool Next(false);
		NextEndPattern = (*++it_Occ).second;
		--it_Occ;
		
		// Forward_check_in
		while((*++it_SDB).first != -1 && (*it_SDB).first != -2)
		{
			if ((*it_SDB).first > 0)
			{
				int new_sup(occ_sup_in[(*it_SDB).first]);
				if (new_sup >= _supmin)
				{
					build_ProjectedBD(new_sup, true, it_Occ->first, it_SDB, NewOccurrences);
				}
			}
		}
		// Forward_check_out
		if ( (*it_SDB).first != -2 && depth < _nb_itemset_max) // si on ne s'est pas arreté sur un changement de séquence
		{ 
			posistion = 0;
			while((*++it_SDB).first != -2)
			{
				if (NextEndPattern == it_SDB)
				{
					Next = true;
				}
				if (posistion <= _gap_max)
				{
					if (posistion >= _gap_min)
					{
						if ((*it_SDB).first > 0)
						{
							int new_sup(occ_sup_out[(*it_SDB).first]);
							if (new_sup >= _supmin)
							{
								build_ProjectedBD(new_sup, false, it_Occ->first, it_SDB, NewOccurrences);
							}
						}
					}
					if ((*it_SDB).first == -1)
					{
						++posistion;
						if (_gap_min == 0) // si pas de gap min, on peut traiter par séquence
						{
							if (Next)
							{
								break;
							}
						}
					}
				}
				else
					break;
			}
		}
	}
}

void build_ProjectedBD(int support, bool itemset, SDB::const_iterator PosBegin, SDB::const_iterator PosEnd, ProjectedDB &NewOccurrences)
{
	int value = itemset?-(*PosEnd).first:(*PosEnd).first;
	TOccurrence Occ(PosBegin,PosEnd);
	if (NewOccurrences.find(value) == NewOccurrences.end())
	{
		NewOccurrences[value].first = support; // ajout dans la table des occurrences global
	}
	NewOccurrences[value].second.push_back(Occ);
}

void support_count(	int value,
			set_int &current_, 
			int &sup, 
			vector<int> & map_extension,
			int id_seq
  		)
{
	if (current_.find(value) == current_.end())
	{
		++sup;
		current_.insert(value); // on le compte pour la séquence courante
		map_extension.push_back(id_seq);
	}
}