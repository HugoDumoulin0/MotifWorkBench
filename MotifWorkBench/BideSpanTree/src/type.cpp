#include "type.hpp"
#include <iostream>
#include <fstream>
#include <boost/algorithm/string.hpp>
 
using namespace std;

SDB New_SDB;

int _supmin = 2;
int _gap_min = 0;
int _gap_max = 1000000;
int _thread = 1;
int _or_is_itemset = 0;
string Corpus;
map_list_sum MLSum;
vector<int> _or;
vector<int> _in;
map_list_pattern MLPattern;
int _nb_itemset_min = 1;
int _nb_itemset_max = 1000000;
Noeud * _NULL_;
int _begin_with_in = 0;

void Load_ini(void){
	ifstream fichier("Load.ini", ios::in);
        if(fichier)
        {      
                string line;
		_NULL_ = new(Noeud);
		while(getline(fichier, line)){
			if (line.find(';')){
				vector< string > Tab_line;
				boost::algorithm::split( Tab_line, line , boost::algorithm::is_any_of("="), boost::algorithm::token_compress_on );
				if (Tab_line[0] == "MINSUP")
				{
					_supmin = atoi(Tab_line[1].c_str());
				
				}
				else
				{
					if(Tab_line[0] == "THREAD")
					{
						_thread = atoi(Tab_line[1].c_str());
					}
					else
					{
							if (Tab_line[0] == "GAPMIN")
							{
								_gap_min = atoi(Tab_line[1].c_str());
							}
							else
							{
								if (Tab_line[0] == "GAPMAX")
								{
									_gap_max = atoi(Tab_line[1].c_str());
								}
								else
								{	
									if (Tab_line[0] == "CORPUS")
									{
										Corpus = Tab_line[1];
									}
									else
									{
										if (Tab_line[0] == "NB_ITEMSET_MIN")
										{
											_nb_itemset_min = atoi(Tab_line[1].c_str());
										}
										else
										{
											if (Tab_line[0] == "NB_ITEMSET_MAX")
											{
												_nb_itemset_max = atoi(Tab_line[1].c_str());
											}
											else
											{
												if (Tab_line[0] == "IN")
												{
													vector< string > Tab_P;
													boost::algorithm::split( Tab_P, Tab_line[1] , boost::algorithm::is_any_of(","), boost::algorithm::token_compress_on );
													for (uint i = 0 ; i < Tab_P.size() ; ++i){
														_in.push_back(atoi(Tab_P[i].c_str()));
													}
												}
												else
												{
													
													if (Tab_line[0] == "OR")
													{
														vector< string > Tab_P2;
														boost::algorithm::split( Tab_P2, Tab_line[1] , boost::algorithm::is_any_of(","), boost::algorithm::token_compress_on );
														for (uint i = 0 ; i < Tab_P2.size() ; ++i){
															_or.push_back(atoi(Tab_P2[i].c_str()));
														}
													}
													else
													{
														if (Tab_line[0] == "BEGINWITH")
														{
															_begin_with_in = atoi(Tab_line[1].c_str());
														}
													}
												}
											}
										}
									}
								}
							}
						
					}
				}
			}
		}
                fichier.close();
        }
        else{
		cerr << "Fichier Load.ini introuvable" << endl;
		exit(EXIT_FAILURE);
	}
}