#include <iostream>
#include <fstream>
#include <sstream>
#include <omp.h>
#include <ctime>
#include "main.hpp"
#include "backward.hpp"
#include "forward.hpp"

extern string Corpus;
extern SDB New_SDB;
extern int _gap_min;
extern int _gap_max;
extern int _supmin;
extern map_list_sum MLSum;
extern map_list_pattern MLPattern;
extern Noeud * _NULL_;
extern int _thread;
extern vector<int> _or;
extern vector<int> _in;
extern int _nb_itemset_max;
extern int _nb_itemset_min;
extern int _or_is_itemset;
extern int _begin_with_in;

int main(int argc, char **argv)
{
	cerr << "Loading dataset" << endl;
	Load_ini();
	map_int support_lenght1;
	Sum_sequences SSeq;
	New_SDB = Load_SDB(Corpus, support_lenght1, SSeq);
	ProjectedDB Size1Item;
	New_SDB = Prun_no_freq(support_lenght1, Size1Item);
	cerr << "SDB loaded" << endl;
	
	SequentialPattern P;
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
			// appartenance
			prec_appartenance_in = false;
			vector <bool> _inbool;
			for (uint indice = 0 ; indice < _in.size() ; ++indice){
				if (_in[indice] == it->first){
					_inbool.push_back(true);
					prec_appartenance_in = true;
				}else{
					_inbool.push_back(false);
				}
			}
			vector <bool> _orbool;
			for (uint indice = 0 ; indice < _or.size() ; ++indice){
				if (_or[indice] == it->first){
					_orbool.push_back(true);
				}else{
					_orbool.push_back(false);
				}
			}
			PGrowth(P, it->first, (*it).second, SSeq[it->first], _orbool, _inbool, 1, prec_appartenance_in, 1);
			
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
			ProjectedDB::iterator it(Keys[i]);
			nb_of_iteration++;		
			std::ostringstream pattern;
			pattern << it->first;
			// appartenance
			prec_appartenance_in = false;
			vector <bool> _inbool;
			for (uint indice = 0 ; indice < _in.size() ; ++indice){
				if (_in[indice] == it->first){
					_inbool.push_back(true);
					prec_appartenance_in = true;
				}else{
					_inbool.push_back(false);
				}
			}
			vector <bool> _orbool;
			for (uint indice = 0 ; indice < _or.size() ; ++indice){
				if (_or[indice] == it->first){
					_orbool.push_back(true);
				}else{
					_orbool.push_back(false);
				}
			}
			PGrowth(P, it->first, (*it).second, SSeq[it->first], _orbool, _inbool, 1, prec_appartenance_in, 1);
		}
	}
	
	cerr << "Pattern Built" << endl;		
	Remove_NoClosed();
	cerr << "No closed patterns removed" << endl;
	PrintResult(MLSum);
	return 0;
}

int vector_size(const SequentialPattern &P)
{
	int result = 0;
	list <list <int > >::const_iterator itJ(P.begin()), End_itJ(P.end());
	for (;itJ!=End_itJ;++itJ) // pour chaque itemset
	{
		result+=itJ->size();
	}
	return result;
}

struct SortBySize
{
   inline bool operator() (const SequentialPattern & lhs, const SequentialPattern  & rhs) const
   {
      return vector_size(lhs) > vector_size(rhs);
   }
};

void Remove_NoClosed()
{
	map_list_pattern::iterator Begin_it(MLPattern.begin()), End_it(MLPattern.end());
	vector <map_list_pattern::iterator> Keys;
	for (;Begin_it!=End_it;++Begin_it){
		Keys.push_back(Begin_it);
	}
	
	size_t i;
	for (i = 0 ; i < Keys.size() ; ++i)
	{
		map_list_pattern::iterator it(Keys[i]);
		if (MLSum.find(it->first) == MLSum.end()) // création d'un nouvel arbre pour le support donné
		{
			Arbre Node;
			Node.hauteur = 0;
			Node.racine = new(Noeud);
			Node.racine->frere = _NULL_;
			Node.racine->fils = _NULL_;
			{
				MLSum[it->first].second = Node;
				MLSum[it->first].first = it->second.first;
			}
		}
		it->second.second.sort(SortBySize());
		list<SequentialPattern>::iterator itI(it->second.second.begin()), End_itI(it->second.second.end());
		for (;itI!=it->second.second.end();++itI) // pour chaque motif trié
		{	
			{
				TesterOuAjouter(*itI, MLSum[it->first].second);
			}
		}
		
	}
}

void Print1Pattern(SequentialPattern &P)
{
	list <list <int > >::const_iterator itJ(P.begin()), End_itJ(P.end());
	for (;itJ!=End_itJ;++itJ) // pour chaque itemset
	{
		printf("{");
		list<int>::const_iterator itK(itJ->begin()), End_itK(itJ->end());
		printf("%i",*itK);
		for (;++itK!=End_itK;) // pour chaque item
		{
			printf(",%i",*itK);
		}
		printf("} ");
	}
	cout << endl;
}

int PGrowth(SequentialPattern Prefix, int Suffix, SeqPattern &SeqPat, uint64_t SumSeq, vector <bool > &_orbool, vector <bool > &_inbool, int depth, bool appartenance_in, int next)
{
	int hasForwardExtention = 0;
	int hasBackwardExtention = 0;
	int pruning = 0;
	ProjectedDB NewOccurrences;
// 	PValue P;
	Sum_sequences SSeqLocal;
	bool appartenance;
	bool appartenance_ones;
	bool prec_appartenance_in = appartenance_in;	
	if (Suffix > 0)
	{
		list <int> P;
		P.push_back(Suffix);
		Prefix.push_back(P); // ajout dans un nouvel itemset
	}
	else
	{
		Prefix.back().push_back(-Suffix); // ajout dans le même itemset
	}
	
	if (depth > _nb_itemset_max)
		return 0;
	
	if (!_begin_with_in)
	{
		Backward_check(hasBackwardExtention, SeqPat, pruning, depth);
		if (pruning)
		{
			return 0;
		}
	}
	
	Forward_check(hasForwardExtention, SeqPat, NewOccurrences, SSeqLocal, depth);
	if (!(hasBackwardExtention || hasForwardExtention) && depth >= _nb_itemset_min)
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
		
		if (appartenance && appartenance_ones && ((_begin_with_in && prec_appartenance_in) || !_begin_with_in))
		{
			#pragma omp critical
			{
				MLPattern[SeqPat.first].second.push_back(Prefix); // version support
				MLPattern[SeqPat.first].first = SeqPat.first;
			}
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
			prec_appartenance_in = appartenance_in;
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
			if ((_begin_with_in && prec_appartenance_in) || !_begin_with_in)
			{
				PGrowth(Prefix, val, (*it).second, SSeqLocal[val], _orbool_next, _inbool_next, depth+1, prec_appartenance_in, 0);
			}
		}
		else // dans un itemset existant
		{
			pattern << -val;
			vector <bool> _inbool_next;
			prec_appartenance_in = appartenance_in;
			for (uint indice = 0 ; indice < _in.size() ; ++indice){
				if (_in[indice] == -val){
					_inbool_next.push_back(true||_inbool[indice]);
					prec_appartenance_in = true;
				}else{
					_inbool_next.push_back(false||_inbool[indice]);
				}
			}
			vector <bool> _orbool_next;
			for (uint indice = 0 ; indice < _or.size() ; ++indice){
				if (_or[indice] == -val){
					_orbool_next.push_back(true||_orbool[indice]);
				}else{
					_orbool_next.push_back(false||_orbool[indice]);
				}
			}
			PGrowth(Prefix, val, (*it).second, SSeqLocal[val], _orbool_next, _inbool_next, depth, prec_appartenance_in, 0);
		}
	}
	return 0;
}

void PrintResult(map_list_sum &MLSum)
{
	map_list_sum::const_iterator it(MLSum.begin()), End_it(MLSum.end());
	for (;it!=End_it;++it)
	{
		string Pattern = "";
		EcrireMotifs(it->second.second.racine->fils, Pattern, it->second.first);
	}
}

void EcrireMotifs(Noeud * courant, string &m, int support)
{
	if (courant != _NULL_)
	{
		std::ostringstream pattern;
		Itemset::const_iterator itS(courant->Value.begin()), End_itS(courant->Value.end());
		pattern << "{" << *itS;
		for (;++itS!=End_itS;)
		{
			pattern  << "," << *itS;
		}
		pattern << "} " ;
		string P( m + pattern.str() );
		if (courant->fils == _NULL_)
		{
			printf("%s: %i\n",P.c_str(), support);
		}
		else
		{
			EcrireMotifs(courant->fils, P, support);
		}
		if (courant->frere != _NULL_)
		{
			EcrireMotifs(courant->frere, m , support);
		}
	}
}

void TesterOuAjouter(SequentialPattern &m, Arbre &a)
{
	SequentialPattern::iterator Pos = m.begin();
	if ((size_t)a.hauteur < m.size())
	{
		a.hauteur = m.size();
		vector<Noeud *> Chemin;	
		list<int>::const_iterator itK(a.racine->Value.begin()), End_itK(a.racine->Value.end());
		Chemin.push_back(a.racine);
		matchRev(m, a.racine->fils, a.racine, Pos, Chemin);
		insereMotif(m, a.racine->fils, Pos);
	}
	else{
		if (!match(m, a.racine->fils, Pos)) // AJOUT ->fils partout...
		{
			vector<Noeud *> Chemin;	
			list<int>::const_iterator itK(a.racine->Value.begin()), End_itK(a.racine->Value.end());
			Chemin.push_back(a.racine);
			matchRev(m, a.racine->fils, a.racine, Pos, Chemin);
			insereMotif(m, a.racine->fils, Pos);
		}
	}
}

bool match(SequentialPattern &m, Noeud * courant, SequentialPattern::iterator Pos)
{
	if (Pos == m.end())
	{
		return true;
	}
	else
	{
		if (courant == _NULL_) //feuille
		{
			return false;
		}
		else
		{
			if (Included(*Pos, courant->Value))
			{

				if (match(m, courant->fils, ++Pos))
				{
					return true;
				}
				--Pos;
			}
			else
			{
				if (match(m, courant->fils, Pos))
				{
					return true;
				}
			}
			return match(m, courant->frere, Pos);
		}
	}
}

void matchRev(SequentialPattern &m, Noeud * courant, Noeud * racine, SequentialPattern::iterator &Pos, vector<Noeud *> &Chemin)
{
	if (courant != _NULL_)
	{
		Noeud * tempFrere = courant->frere;
		vector<Noeud *> CheminTemp;
		CheminTemp = Chemin;
		if (courant->fils == _NULL_) //feuille
		{
			if (RecIncluded(courant->Value, Pos, m) != m.end()) // AJOUT
			{
				Chemin.push_back(courant);
				detruire(Chemin, racine);
			}
		}
		else
		{
			SequentialPattern::iterator PosTemp;
			PosTemp = RecIncluded(courant->Value, Pos, m);
			if (PosTemp != m.end())
			{
				Chemin.push_back(courant);
				matchRev(m, courant->fils, racine, ++PosTemp, Chemin);
			}
		}
		if (tempFrere != _NULL_)
		{
			matchRev(m, tempFrere, racine, Pos, CheminTemp);
		}
	}

}

SequentialPattern::iterator RecIncluded(Itemset & I, SequentialPattern::iterator Pos, SequentialPattern & P) // cherche si l'itemset I est inclu dans le motif P
{
	while(Pos != P.end())
	{
		if (Included(I, *Pos))
		{
			return Pos;
		}
		else
		{
			++Pos;
		}
	}
	return Pos;
}

Noeud * returnFrereG(vector <Noeud* > Chemin, int pos, Noeud * racine)
{
	Noeud * premierfils = Chemin[pos-1]->fils;
	while (premierfils->frere != Chemin[pos])
	{
		premierfils = premierfils->frere;
	}
	return premierfils;
}

void detruire(vector <Noeud* > Chemin, Noeud * racine)
{
	bool continuer = true;
	int pos = Chemin.size()-1;
	Noeud * prec;
	while (continuer)
	{
		if (Chemin[pos-1]->fils == Chemin[pos])
		{
// 			cout << "fils = père.fils" << endl;
			if (Chemin[pos]->frere == _NULL_)
			{
				Chemin[pos-1]->fils = _NULL_;
				delete(Chemin[pos]);
			}
			else
			{
				Chemin[pos-1]->fils = Chemin[pos]->frere;
				delete(Chemin[pos]);
				continuer = false;
			}
		}
		else
		{
			prec = returnFrereG(Chemin, pos, racine);
			prec->frere = Chemin[pos]->frere;
			delete(Chemin[pos]);
			continuer = false;

		}
		if (Chemin[pos-1] == racine)
		{
			continuer = false;
		}
		else
		{
			--pos;
		}
	}
}


void insereMotif(SequentialPattern &m, Noeud * &courant, SequentialPattern::iterator Pos)
{

	if (courant == _NULL_)
	{

		courant = insere(m, courant, Pos);
	}
	else
	{
		if (courant->Value == *Pos) // AJOUT == à la place du included
		{
			insereMotif(m, courant->fils, ++Pos);
		}
		else
		{
			if (courant->Value > *Pos)
			{

				courant = insere(m, courant, Pos);
			}
			else
			{
				insereMotif(m, courant->frere, Pos);
			}
		}
	}
}

Noeud * insere(SequentialPattern &m, Noeud * courant, SequentialPattern::iterator &Pos)
{
	Noeud * result;
	if (courant == _NULL_)
	{
		courant = new(Noeud);
		courant->Value = *Pos;
		courant->fils = _NULL_;
		courant->frere = _NULL_;
	}
	else
	{
		Noeud * New = new(Noeud);
		New->fils = courant->fils; // AJOUT car sinon on ne duplique pas les fils de l'ancien motif
		New->Value = courant->Value;
		courant->Value = *Pos;
		New->frere = courant->frere;
		courant->frere = New;
	}
	result = courant;
	while (++Pos != m.end())
	{
		courant->fils = new(Noeud);
		courant->fils->Value = *Pos;
		courant = courant->fils;
		courant->frere = _NULL_;
	}
	
	courant->fils = _NULL_;
	return result;
}



bool Is_in(SequentialPattern & P2, SequentialPattern & P1) // pour tester tout le motif
{
	uint result = 0;
	list <list <int > >::iterator it2(P2.begin()), End_it2(P2.end()), it1(P1.begin()), End_it1(P1.end());
	for (;it2!=End_it2;++it2)
	{
		for (;it1!=End_it1;)
		{
			if (it1->size() >= it2->size())
			{
				if (Included(*it2, *it1))
				{
					++result;
					++it1;
					break;
				}
			}
			++it1;
		}
	}
	return result == P2.size();
}

bool Included( Itemset & V1,  Itemset & V2)
{
	bool result = false;
	Itemset::const_iterator it1(V1.begin()), End_it1(V1.end());
	Itemset::const_iterator it2(V2.begin()), End_it2(V2.end());
	for (;it1!=End_it1;++it1)
	{
		result = false;
		for (;!result && *it1 >= *it2 && it2!=End_it2;++it2)
		{
			result = result || *it1 == *it2;
		}
		if (!result)
		{
			return result;
		}
	}
	return result;
}

void support_count(int value, set_int &current_, map_int &sup_, int seq_id, Sum_sequences &SSeq)
{
	if (current_.find(value) == current_.end())
	{
		++sup_[value];
		SSeq[value]+=seq_id;
		current_.insert(value);
	}
}

SDB Load_SDB(string & Corpus_to, map_int & support_lenght1, Sum_sequences &SSeq)
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
					{ // si on ne suis pas une nouvelle séquence (car sinon le -2 implique un chagement d'itemset donc pas besoin d'ajouter de -1
						
						pair_int PInt(-1, 0);
						SDB_.push_back(PInt);
					}
					itemset_c = itemset;
				}
				pair_int PInt(value, seq_id);
				SDB_.push_back(PInt);
				support_count(value, current_item, support_lenght1, seq_id, SSeq);
			}
		}
		pair_int PInt(-2, 0);
		SDB_.push_back(PInt);
		fichier.close();
		// ATTENTION, PROBLÈME DE DOUBLON LIE À GEdit QUI AJOUTE UN ESPACE À LA FIN DU FICHIER DE MOTIFS...
	}
	else{
		cerr << "failed to open corpus" << endl;
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
				Size1Item[P].second.push_back(Occ);// ajout de l'occurrences dans la table des occurrences
			}
			else
			{
				pair_int PInt(0, 0);
				SDB_.push_back(PInt);
			}
		}
	}
	return SDB_;
}