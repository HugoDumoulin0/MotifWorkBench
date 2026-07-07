#ifndef MAIN_H
#define MAIN_H

	#include "type.hpp"
	
	SDB Load_SDB
	(
		string & Corpus_to, 
		map_int & support_lenght1,
		Sum_sequences &SSeq
	);
	
	void support_count
	(
		int, 
		set_int &current_,
		map_int &sup_,
		int seq_id, 
		Sum_sequences &SSeq
	);
	
	SDB Prun_no_freq
	(
		map_int & length1_support_SDB_new, 
		ProjectedDB & Size1Item
	);
	
	int PGrowth
	(
		SequentialPattern Prefix,
		int Suffix,
		SeqPattern & SeqPat,
		uint64_t SumSeq,
		vector <bool> & _orbool, 
		vector <bool > &_inbool,
		int depth,
		bool appartenance_in,
		int next
	);
	
	void Remove_NoClosed
	();

	bool Is_in
	(
		SequentialPattern & P2, 
		SequentialPattern & P1
	);
	
	bool Included
	(
		Itemset & V1,
		Itemset & V2
	);

	void PrintPattern
	();
	
	void Print1Pattern
	(
		SequentialPattern &P
	);
	
	int vector_size
	(
		const SequentialPattern &P
	);
	
	void TesterOuAjouter
	(
		SequentialPattern &m,
		Arbre &a
	);
	
	bool match(SequentialPattern &m, Noeud * racine, SequentialPattern::iterator Pos);


	void matchRev(SequentialPattern &m, Noeud * racine, Noeud * racineSAV, SequentialPattern::iterator &Pos, vector<Noeud *> &Chemin);


	void insereMotif(SequentialPattern &m, Noeud * &racine, SequentialPattern::iterator Pos);
	
	Noeud * insere(SequentialPattern &m, Noeud * racine, SequentialPattern::iterator &Pos);
	
	void PrintResult(map_list_sum &MLSum);
	
	void EcrireMotifs(Noeud * courant, string &m, int support);
	
	void detruire(vector <Noeud* > Chemin, Noeud * racine);
	
	SequentialPattern::iterator RecIncluded(Itemset & V1, SequentialPattern::iterator Pos, SequentialPattern & P);
	
	Noeud * returnFrereG(vector <Noeud* > Chemin , int pos, Noeud * racine);

	Noeud * returnFrereGR(vector <Noeud* > Chemin, int pos, Noeud * racine);

#endif //MAIN_H