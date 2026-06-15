#include "type.hpp"
#include <iostream>
#include <fstream>
 
using namespace std;

static vector<string> split_tokens(const string &value, char separator)
{
	vector<string> tokens;
	string current;
	for (size_t i = 0; i < value.size(); ++i) {
		char ch = value[i];
		if (ch == separator) {
			if (!current.empty()) {
				tokens.push_back(current);
				current.clear();
			}
		} else {
			current += ch;
		}
	}
	if (!current.empty()) {
		tokens.push_back(current);
	}
	return tokens;
}

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
				vector< string > Tab_line = split_tokens(line, '=');
				if (Tab_line.empty()){
					continue;
				}
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
													vector< string > Tab_P = split_tokens(Tab_line[1], ',');
													for (size_t i = 0 ; i < Tab_P.size() ; ++i){
														_in.push_back(atoi(Tab_P[i].c_str()));
													}
												}
												else
												{
													
													if (Tab_line[0] == "OR")
													{
														vector< string > Tab_P2 = split_tokens(Tab_line[1], ',');
														for (size_t i = 0 ; i < Tab_P2.size() ; ++i){
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
