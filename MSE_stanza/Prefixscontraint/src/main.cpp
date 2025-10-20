#include <iostream>
#include <fstream>
#include <sstream>
#include <omp.h>
#include <ctime>
#include <cstdio>
#include "main.hpp"
#include "forward.hpp"

extern string Corpus;
extern SDB New_SDB;
extern int _gap_min;
extern int _gap_max;
extern int _supmin;
extern vector<int> _or;
extern vector<int> _in;
extern int _nb_itemset_max;
extern int _nb_itemset_min;
extern int _or_is_itemset;
extern int _thread;


int main(int argc, char **argv)
{
// 	cerr << "Loading dataset" << endl;
	Load_ini();
	map_int support_lenght1;
	map_extension extension; // pour les motifs de taille 1
	New_SDB = Load_SDB(Corpus, support_lenght1, extension);
	ProjectedDB Size1Item;
	New_SDB = Prun_no_freq(support_lenght1, Size1Item);
	string P;
	bool prec_appartenance_in = false;
	int nb_of_iteration = 0;
	
	if (_thread == 1)
	{
		ProjectedDB::iterator it(Size1Item.begin()), End_it(Size1Item.end());
		for (;it!=End_it;++it)
		{
			nb_of_iteration++;
			std::ostringstream pattern;
			pattern << it->first;
			string P = "{"+pattern.str();
			// appartenance
			prec_appartenance_in = false;
			vector <bool> _inbool;
			for (uint indice = 0 ; indice < _in.size() ; ++indice){
				if (_in[indice] == it->first){
					_inbool.push_back(true);
				}else{
					_inbool.push_back(false);
				}
			}
			vector <bool> _orbool;
			for (uint indice = 0 ; indice < _or.size() ; ++indice){
				if (_or[indice] == it->first){
					_orbool.push_back(true);
					prec_appartenance_in = true;
				}else{
					_orbool.push_back(false);
				}
			}
			PGrowth(P, (*it).second, _orbool, _inbool, 1, prec_appartenance_in, 1, extension[it->first]);
		}
	}
	else
	{
		ProjectedDB::iterator Begin_it = Size1Item.begin(), End_it(Size1Item.end());
		vector <ProjectedDB::iterator> Keys;
		for (;Begin_it!=End_it;++Begin_it){
			Keys.push_back(Begin_it);
		}
		
		size_t i;
		#pragma omp parallel for private(i) num_threads(_thread) schedule(dynamic)
		for (i = 0 ; i < Keys.size() ; ++i)
		{
			nb_of_iteration++;
			ProjectedDB::iterator it(Keys[i]);
			std::ostringstream pattern;
			pattern << it->first;
			string P = "{"+pattern.str();
			// appartenance
			prec_appartenance_in = false;
			vector <bool> _inbool;
			for (uint indice = 0 ; indice < _in.size() ; ++indice){
				if (_in[indice] == it->first){
					_inbool.push_back(true);
				}else{
					_inbool.push_back(false);
				}
			}
			vector <bool> _orbool;
			for (uint indice = 0 ; indice < _or.size() ; ++indice){
				if (_or[indice] == it->first){
					_orbool.push_back(true);
					prec_appartenance_in = true;
				}else{
					_orbool.push_back(false);
				}
			}
			PGrowth(P, (*it).second, _orbool, _inbool, 1, prec_appartenance_in, 1, extension[it->first]);
		}
	}
// 	cerr << "Pattern Built" << endl;
	return 0;
}

int PGrowth(string Prefix, SeqPattern &SeqPat, vector <bool > &_orbool, vector <bool > &_inbool, int depth, bool appartenance_in, int next, vector<int> & extension)
{
	ProjectedDB NewOccurrences;
	string P;
	bool appartenance;
	bool appartenance_ones;
	bool prec_appartenance_in = false;
	map_extension extension_in;
	map_extension extension_out;
	
	if (depth > _nb_itemset_max)
		return 0;
	
	Forward_check(SeqPat, NewOccurrences, depth, extension_in, extension_out);
	if (depth >= _nb_itemset_min)
	{
		appartenance = true;
		for (uint indice = 0 ; indice < _inbool.size() ; ++indice){
			appartenance = appartenance && _inbool[indice];
		}
		if (!_orbool.size()){
			appartenance_ones = true;
		}else{
			appartenance_ones = false;
			for (uint indice = 0 ; indice < _orbool.size() ; ++indice){
				appartenance_ones = appartenance_ones || _orbool[indice];
			}
		}
		if (appartenance && appartenance_ones){
			std::ostringstream ext;
			ext << extension[0];
// 			string extensionStr = "["+ext.str() ;
			string extensionStr = ext.str() ;
			for (uint i = 1 ; i < extension.size() ; ++i) {
				std::ostringstream ext;
				ext << extension[i];
				extensionStr += ";"+ext.str();
			}
// 			extensionStr += "]";
			printf("%s} : %i : %s\n", Prefix.c_str(), SeqPat.first, extensionStr.c_str());
		}
	}
	
	ProjectedDB::iterator it(NewOccurrences.begin()), End_it(NewOccurrences.end());
	for (;it!=End_it;++it)
	{
		std::ostringstream pattern;
		int val = it->first;
		if (val > 0) // dans un nouvel itemset
		{
			pattern << val;
			
			vector <bool> _inbool_next;
			prec_appartenance_in = false;
			for (uint indice = 0 ; indice < _in.size() ; ++indice){
				if (_in[indice] == val){
					_inbool_next.push_back(true||_inbool[indice]);
				}else{
					_inbool_next.push_back(false||_inbool[indice]);
				}
			}
			vector <bool> _orbool_next;
			for (uint indice = 0 ; indice < _or.size() ; ++indice){
				if (_or[indice] == val){
					_orbool_next.push_back(true||_orbool[indice]);
					prec_appartenance_in = true;
				}else{
					_orbool_next.push_back(false||_orbool[indice]);
				}
			}
			
			PGrowth(Prefix+"} {"+pattern.str(), (*it).second, _orbool_next, _inbool_next, depth+1, prec_appartenance_in, 0 , extension_out[val]);
		}
		else // dans un itemset existant
		{
			
			pattern << -val;
			
			vector <bool> _inbool_next;
			prec_appartenance_in = false;
			for (uint indice = 0 ; indice < _in.size() ; ++indice){
				if (_in[indice] == -val){
					_inbool_next.push_back(true||_inbool[indice]);
				}else{
					_inbool_next.push_back(false||_inbool[indice]);
				}
			}
			vector <bool> _orbool_next;
			for (uint indice = 0 ; indice < _or.size() ; ++indice){
				if (_or[indice] == -val){
					_orbool_next.push_back(true||_orbool[indice]);
					prec_appartenance_in = true;
				}else{
					_orbool_next.push_back(false||_orbool[indice]);
				}
			}
			
			PGrowth(Prefix+','+pattern.str(), (*it).second, _orbool_next, _inbool_next, depth, prec_appartenance_in, 1, extension_in[-val]);
		}
	}
	
	return 0;
}

void support_count(int value, set_int &current_, map_int &sup_, vector<int> & extension, int seq_id )
{
	if (current_.find(value) == current_.end())
	{
		++sup_[value];
		current_.insert(value);
		extension.push_back(seq_id);
	}
}

SDB Load_SDB(string & Corpus_to, map_int & support_lenght1, map_extension & extension)
{
	ifstream fichier(Corpus_to.c_str(), ios::in);
	
	SDB SDB_;
	int seq_id = 0;
	if(!fichier.fail())
	{
		string current ;
		int itemset_c = 1;
		set_int current_item;
		int value, itemset;
		
		while(!fichier.eof())
		{
			fichier >> current >> value;
			if (!current.compare("seqId"))
			{ // new sequence
				pair_int PInt(-2, 0);
				++seq_id;
				SDB_.push_back(PInt);
				current_item.clear();
			}else
			{	
				itemset = atoi(current.c_str());
				if (itemset_c != itemset)
				{ // new itemset
					if (current_item.size())
					{ // si on ne suit pas une nouvelle séquence (car sinon le -2 implique un chagement d'itemset donc pas besoin d'ajouter de -1
						
						pair_int PInt(-1, 0);
						SDB_.push_back(PInt);
					}
					itemset_c = itemset;
				}
				pair_int PInt(value, seq_id);
				SDB_.push_back(PInt);
				support_count(value, current_item, support_lenght1, extension[value], seq_id);
//                                 fprintf(stderr, "item %i, seq %i\n", value, seq_id);
			}
		}
		pair_int PInt(-2, 0);
		SDB_.push_back(PInt);
		fichier.close();
	}
	return SDB_;

}

SDB Prun_no_freq(map_int & length1_support_SDB, ProjectedDB & Size1Item)
{
	SDB SDB_;
	SDB::const_iterator it_SDB(New_SDB.begin()) , End_it_SDB(New_SDB.end());
	for (;it_SDB!=End_it_SDB;++it_SDB)
	{
		if ((*it_SDB).first < 0)
		{
			SDB_.push_back(*it_SDB);
		}
		else
		{
			if (length1_support_SDB[(*it_SDB).first] >= _supmin)
			{
				int P = (*it_SDB).first;
				SDB_.push_back(*it_SDB);
				TOccurrence Occ(it_SDB,it_SDB);
				if (Size1Item.find(P) == Size1Item.end())
				{
					Size1Item[P].first = length1_support_SDB[(*it_SDB).first]; // ajout du support dans la table des occurrences
				}
				Size1Item[P].second.push_back(Occ);// ajout de l'occurrence dans la table des occurrences
			}
			else
			{
				pair_int PInt(0, 0);
				SDB_.push_back(PInt);
			}
		}
	}
// 	cerr << "SDB loaded" << endl;
	return SDB_;
}