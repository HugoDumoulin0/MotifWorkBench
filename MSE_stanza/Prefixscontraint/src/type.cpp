#include "type.hpp"
#include <iostream>
#include <fstream>
// #include <boost/algorithm/string.hpp>
 
using namespace std;

SDB New_SDB;

int _supmin = 2;
int _gap_min = 0;
int _gap_max = 1000000;
int _thread = 1;
string Corpus;
vector<int> _or;
vector<int> _in;
int _nb_itemset_min = 1;
int _nb_itemset_max = 1000000;
int _or_is_itemset = 0;

void Load_ini(void){
	ifstream fichier("../config/Load.ini", ios::in);
        if(fichier)
        {      
                string line;
		while(getline(fichier, line))
		{
			if (line.find(';'))
			{
				std::size_t found = line.find('=');
				if (found!=std::string::npos)
				{
					vector< string > Tab_line;
					Tab_line.push_back(line.substr(0,found)); // avant le ';'
					Tab_line.push_back(line.substr(found+1)); // après le ';'
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
									if (Tab_line[0] == "GAPMAX"){
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
											if (Tab_line[0] == "NB_ITEMSET_MIN"){
												_nb_itemset_min = atoi(Tab_line[1].c_str());
											}else{
												if (Tab_line[0] == "NB_ITEMSET_MAX"){
													_nb_itemset_max = atoi(Tab_line[1].c_str());
												}else{
													if (Tab_line[0] == "OR_IS_ITEMSET"){
														_or_is_itemset = atoi(Tab_line[1].c_str());
													}else{
														if (Tab_line[0] == "IN")
														{
															string s(Tab_line[1]);
															string delimiters = ",";
															size_t current;
															size_t next = -1;
															do
															{
																current = next + 1;
																next = s.find_first_of( delimiters, current );
																_in.push_back(atoi(s.substr( current, next - current ).c_str()));
															}
															while (next != string::npos);
														}
														else
														{
															
															if (Tab_line[0] == "OR")
															{
																string s(Tab_line[1]);
																string delimiters = ",";
																size_t current;
																size_t next = -1;
																do
																{
																	current = next + 1;
																	next = s.find_first_of( delimiters, current );
																	_or.push_back(atoi(s.substr( current, next - current ).c_str()));
																}
																while (next != string::npos);
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
		}
                fichier.close();
        }
        else
	{
		cerr << "Fichier Load.ini introuvable" << endl;
		exit(EXIT_FAILURE);
	}
}
