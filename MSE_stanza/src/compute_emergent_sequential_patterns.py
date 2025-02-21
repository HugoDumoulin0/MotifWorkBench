import os
import re
import pandas as pd
import pickle as pk
import formate_patterns

def load_df(path_df, sep="\t", encoding="utf-8"):
    return pd.read_csv(path_df, sep=sep, encoding=encoding)

def save_pickles_results(to_save, title_file):
    """
    input: file
    ouput: bool
    do: save the object locally
    """
    try:
        with open(title_file, "wb") as p:
            pk.dump(to_save, p)
        print("\tResults : saved")
        return True
    except:
        return False

def load_pickles(title_file):
    with open(title_file, "rb") as p:
        return pk.load(p)

def get_nbr_seq(dmt4_files):
    with open("{}".format(dmt4_files), 'r', encoding="utf-8") as dmt4 :
        return len([line for line in dmt4.readlines() if "seqId" in line])

def from_txt_to_dict(file_results):
    dict_results = dict()
    with open(file_results, "r+") as file :
        line = file.readline().strip()
        while line :
            elements_line = line.split(":")
            if len(elements_line[0].strip().split(" ")) >= 1:
                dict_results[elements_line[0].strip()] = int(elements_line[1].replace(" ",""))
            line = file.readline().strip()
    save_pickles_results(dict_results, file_results.replace("txt", "pk"))
    return True

def from_dict_to_df(path_emergent_dict):
    emergent_patt = load_pickles(path_emergent_dict)
    df = pd.DataFrame.from_dict(emergent_patt, orient="index", columns=["motifs_int", "motifs_str", "GR", "freq_1", "freq_2"])
    df_sort = df.sort_values(by="GR", ascending=False)
    df_sort.to_csv(path_emergent_dict.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    return True

def compute_GR(type_1, type_2):
    # minsups = ["25", "30", "40"]

    ### remarque : ici le taux de croissance minimal ou growth rate (GR) est fixé à 1
    ## il serait intéressant de le rendre modifiable
    ## il serait intéressant de le remplacer par un indice de spécificité de 2
    ## indice de spécificité avec T = card(D union D') ; t = card(D) ; f = couverture totale dans D et D' ; k = couverture dans D

    minsups = ["25"]
    for mins in minsups:
        print(f"\t\tminsup:{mins}")
        dict_1 = load_pickles("./Patterns_results/Closed/{}_00_DMT4_{}_files_sorted_closed.pk".format(mins, type_1))
        dict_2 = load_pickles("./Patterns_results/Freq/{}_00_DMT4_{}_files_sorted_freq.pk".format(mins, type_2))

        nbr_seq_1 = get_nbr_seq("./Data/DMT4_files/DMT4_{}_files_sorted.txt".format(type_1))
        nbr_seq_2 = get_nbr_seq("./Data/DMT4_files/DMT4_{}_files_sorted.txt".format(type_2))
        # 21-02-2025 : nbr_seq_ = number of sentences of the corpus (from conl_dmt4.transform_data, l. 131)


        # lexic_int_str = formate_patterns.load_lexique() ### Modification du script de Jade qui présente un problème ici ####
        lexic_int_str = formate_patterns.make_dict_int_to_str()


        dict_gr = dict()
        index_p = 0
        for p in dict_1:
            freq_1 = dict_1.get(p)
                #21-02-2025: this is absolute freq (number of sentences comprising motif)
            if p in dict_2:
                freq_2 = dict_2.get(p)
                gr = (freq_1 / nbr_seq_1) / (freq_2 / nbr_seq_2)
                    #21-02-2025: freq_1 / nbr_seq_1) = relative freq, i.e., what is called
                    #"frequence" in Mekki PhD (2022: p. 95)
                dict_gr[index_p] = [formate_patterns.from_str_to_list(p),
                                    formate_patterns.from_int_to_str(p, lexic_int_str),
                                    gr,
                                    freq_1, #21-02-2025: it is absolute freq that is written in .tsv
                                    freq_2]
            else:
                gr = freq_1
                dict_gr[index_p] = [formate_patterns.from_str_to_list(p),
                                    formate_patterns.from_int_to_str(p, lexic_int_str),
                                    gr,
                                    (freq_1 / nbr_seq_1), #21-02-2025: it is relative freq that is written in .tsv
                                    0]
            index_p+=1
        file_out = "./Patterns_results/Emergent/{}_00_{}_{}.pk".format(mins,
                                                                       type_1,
                                                                       type_2)
        save_pickles_results(dict_gr, file_out)
        from_dict_to_df(file_out)
    return True

#21-02-2025: There is quite a problem there: GR and freq have different definitions depending on wether
#the motif appears in both corpora or not.
