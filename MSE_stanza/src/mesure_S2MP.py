#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import sys
import pandas as pd
import pickle as pk
import numpy as np
import pprint




########## Step 1: Mapping Score Calculation.

# Mapping


def weight(itemset_1, itemset_2):
    """
    input : set(itemset_1), set(itemset_2) ex : {7}, {2, 7}
    ouput : float(la proportion d'item en commun) ex: 0.75
    """
    return len(itemset_1 & itemset_2) / ((len(itemset_1) + len(itemset_2)) / 2)



def solveConflit(conflict_1, conflict_2, candidat_0, seq_1, seq_2):
    """
    input: 
    ouput: 4 possibles paires mappings 
        1. <(c1, c0)> <c2, nextMaxBefore_c2)>
        2. <(c1, c0)> <c2, nextMaxAfter_c2)>
        3. <(c2, c0)> <(c1, nextMaxBefore_c1)>
        4. <(c2, c0)> <(c1, nextMaxAfter_c1)>
        on garde la paire dont le localSim est le plus élevé
    """
    
    weight_c1_c0 = weight(seq_1[conflict_1], seq_2[candidat_0])
    weight_c2_c0 = weight(seq_1[conflict_2], seq_2[candidat_0])
    
    seq_before_c0 = seq_2[:candidat_0]
    seq_after_c0 =  seq_2[candidat_0+1:]

    localSim_c1c2 = lambda weight_c1_c0, weight_max : (weight_c1_c0 + weight_max)/2
    localSim_c2c1 = lambda weight_c2_c0, weight_max : 0.5*((weight_c2_c0 + weight_max)/2)
    
    scores_localSim = []
    c1c0_c2maxBefore, c1c0_c2maxAfter, c2c0_c1maxBefore, c2c0_c1maxAfter = 0, 0, 0, 0

    if seq_before_c0 == []:

        # 2. <(c1, c0)> <c2, nextMaxAfter_c2)>
        after_weight_conflict_2 = [weight(seq_1[conflict_2], itemset_2) for itemset_2 in seq_after_c0]
        try: 
            max_after_weight_conflict_2 = max(after_weight_conflict_2)
        except:
            max_after_weight_conflict_2 = None

        # 4. <(c2, c0)> <(c1, nextMaxAfter_c1)>
        after_weight_conflict_1 = [weight(seq_1[conflict_1], itemset_2) for itemset_2 in seq_after_c0]
        try :
            max_after_weight_conflict_1 = max(after_weight_conflict_1)
        except: 
            max_after_weight_conflict_1 = None
        
        # localSim -------------------------------

        # 2. <(c1, c0)> <c2, nextMaxAfter_c2)>
        if max_after_weight_conflict_2 != None:
            c1c0_c2maxAfter = localSim_c1c2(weight_c1_c0, max_after_weight_conflict_2)
            scores_localSim.append(c1c0_c2maxAfter)
            
        # 4. <(c2, c0)> <(c1, nextMaxAfter_c1)>
        if max_after_weight_conflict_1 != None:
            c2c0_c1maxAfter = localSim_c2c1(weight_c2_c0, max_after_weight_conflict_1)
            scores_localSim.append(c2c0_c1maxAfter)
            

    if seq_after_c0 == []:

        # 1. <(c1, c0)> <c2, nextMaxBefore_c2)>
        before_weight_conflict_2 = [weight(seq_1[conflict_2], itemset_2) for itemset_2 in seq_before_c0]
        try:
            max_before_weight_conflict_2 = max(before_weight_conflict_2)
        except:
            max_before_weight_conflict_2 = None
            
        # 3. <(c2, c0)> <(c1, nextMaxBefore_c1)>
        before_weight_conflict_1 = [weight(seq_1[conflict_1], itemset_2) for itemset_2 in seq_before_c0]
        try :
            max_before_weight_conflict_1 = max(before_weight_conflict_1)
        except:
            max_before_weight_conflict_1 = None
        
        # localSim -------------------------------

        # 1. <(c1, c0)> <c2, nextMaxBefore_c2)>
        if max_before_weight_conflict_2 != None:
            c1c0_c2maxBefore = localSim_c1c2(weight_c1_c0, max_before_weight_conflict_2)
            scores_localSim.append(c1c0_c2maxBefore)

        # 3. <(c2, c0)> <(c1, nextMaxBefore_c1)>
        if max_before_weight_conflict_1 != None:
            c2c0_c1maxBefore = localSim_c2c1(weight_c2_c0, max_before_weight_conflict_1)
            scores_localSim.append(c2c0_c1maxBefore) 
    
    else: # si candidats avant et après

        # 1. <(c1, c0)> <c2, nextMaxBefore_c2)>
        before_weight_conflict_2 = [weight(seq_1[conflict_2], itemset_2) for itemset_2 in seq_before_c0]
        try : 
            max_before_weight_conflict_2 = max(before_weight_conflict_2)
        except: 
            max_before_weight_conflict_2 = None
        
        # 2. <(c1, c0)> <c2, nextMaxAfter_c2)>
        after_weight_conflict_2 = [weight(seq_1[conflict_2], itemset_2) for itemset_2 in seq_after_c0]
        try: 
            max_after_weight_conflict_2 = max(after_weight_conflict_2)
        except:
            max_after_weight_conflict_2 = None
        
        # 3. <(c2, c0)> <(c1, nextMaxBefore_c1)>
        before_weight_conflict_1 = [weight(seq_1[conflict_1], itemset_2) for itemset_2 in seq_before_c0]
        try :
            max_before_weight_conflict_1 = max(before_weight_conflict_1)
        except:
            max_before_weight_conflict_1 = None
        
        # 4. <(c2, c0)> <(c1, nextMaxAfter_c1)>
        after_weight_conflict_1 = [weight(seq_1[conflict_1], itemset_2) for itemset_2 in seq_after_c0]
        try :
            max_after_weight_conflict_1 = max(after_weight_conflict_1)
        except: 
            max_after_weight_conflict_1 = None
        
        # localSim -------------------------------        
        
        # 1. <(c1, c0)> <c2, nextMaxBefore_c2)>
        if max_before_weight_conflict_2 != None:
            c1c0_c2maxBefore = localSim_c1c2(weight_c1_c0, max_before_weight_conflict_2)
            scores_localSim.append(c1c0_c2maxBefore)
                
        # 2. <(c1, c0)> <c2, nextMaxAfter_c2)>
        if max_after_weight_conflict_2 != None:
            c1c0_c2maxAfter = localSim_c1c2(weight_c1_c0, max_after_weight_conflict_2)
            scores_localSim.append(c1c0_c2maxAfter)
            
        # 3. <(c2, c0)> <(c1, nextMaxBefore_c1)>
        if max_before_weight_conflict_1 != None:
            c2c0_c1maxBefore = localSim_c2c1(weight_c2_c0, max_before_weight_conflict_1)
            scores_localSim.append(c2c0_c1maxBefore)
            
        # 4. <(c2, c0)> <(c1, nextMaxAfter_c1)>
        if max_after_weight_conflict_1 != None:
            c2c0_c1maxAfter = localSim_c2c1(weight_c2_c0, max_after_weight_conflict_1)
            scores_localSim.append(c2c0_c1maxAfter)
            
    # On selectionne la paire qui a le localSim le plus eleve  -------------------------------
    
    if max(scores_localSim) == c1c0_c2maxBefore:
        # 1. <(c1, c0)> <c2, nextMaxBefore_c2)>
        return {conflict_1 :  candidat_0,
                conflict_2 : candidat_0+1 + before_weight_conflict_2.index(max_before_weight_conflict_2)}
        
    if max(scores_localSim) == c1c0_c2maxAfter:
        # 2. <(c1, c0)> <c2, nextMaxAfter_c2)>
        return {conflict_1 :  candidat_0,
                conflict_2 : candidat_0+1 + after_weight_conflict_2.index(max_after_weight_conflict_2)}
        
    if max(scores_localSim) == c2c0_c1maxBefore:
        # 3. <(c2, c0)> <(c1, nextMaxBefore_c1)>
        return {conflict_2 :  candidat_0,
                conflict_1 : candidat_0+1 + before_weight_conflict_1.index(max_before_weight_conflict_1)}
        
    if max(scores_localSim) == c2c0_c1maxAfter:
        # 4. <(c2, c0)> <(c1, nextMaxAfter_c1)>
        return {conflict_2 :  candidat_0,
                conflict_1 : candidat_0+1 + after_weight_conflict_1.index(max_after_weight_conflict_1)}
        


    
def mapping(seq_1, seq_2):
    """
    input : 
    ouput : {index itemset de seq_1 : index itemset_seq_2}
    """
    orderMap = {}
    if len(seq_1) == 1:
        weight_mapping_scores_c2 = [weight(seq_1[0], itemset_2) for itemset_2 in seq_2]
        max_weight_c2 = max(weight_mapping_scores_c2)
        if max_weight_c2 != 0 : 
            max_weight_index_c2 = weight_mapping_scores_c2.index(max_weight_c2)
            orderMap[0] = max_weight_index_c2
            return orderMap
        else:
            pass
    if len(seq_2) == 1: #ici index inversé
        weight_mapping_scores_c1 = [weight(itemset_1, seq_2[0]) for itemset_1 in seq_1]
        max_weight_c1 = max(weight_mapping_scores_c1)
        if max_weight_c1 != 0 : 
            max_weight_index_c1 = weight_mapping_scores_c1.index(max_weight_c1)
            orderMap[max_weight_index_c1] = 0
            return orderMap
        else:
            pass
    else:
        for i, itemset_1 in enumerate(seq_1):
            weight_mapping_scores = [weight(itemset_1, itemset_2) for itemset_2 in seq_2]
            max_weight = max(weight_mapping_scores)
            if max_weight != 0:
                max_weight_index = weight_mapping_scores.index(max_weight)
                # si itemset_seq_2 nest pas encore ete mappe un itemset_seq_1
                if max_weight_index not in orderMap.values():
                    # si il y a égalité entre deux itemset_seq_2 pour etre mappe avec un itemset_seq_1
                    if weight_mapping_scores.count(max_weight) == 2:
                        orderMap[i] = sorted([i for i in range(len(weight_mapping_scores)) if weight_mapping_scores[i] == max_weight])[0]
                    # si pas degalite
                    else:
                        orderMap[i] = max_weight_index
                # si itemeset_seq_2 est deja mappe avec un itemset_seq_1 alors conflit 
                else:
                    conflict_1 = {orderMap[k]:k for k in orderMap}.get(max_weight_index)
                    conflict_2 = i
                    final_candidats = solveConflit(conflict_1, conflict_2, max_weight_index, seq_1, seq_2)
                    orderMap.update(final_candidats)
            else:
                pass

    return orderMap



# AVERAGE WEIGHT SCORE



def GetAveWeightScore (seq_1, seq_2, orderMap): 
    if len(orderMap) != 0:
        return sum([weight(seq_1[i], seq_2[orderMap.get(i)]) for i in range(len(orderMap.keys()))])/len(orderMap)
    else:
        return 0
    


########## Step 2: Order Score Calculation

# TOTAL ORDER

## Chercher les sous séquences croissantes


def get_all_subseq_ascending(orderMap):
    orderMap_Seq = list(orderMap.values())
    val = 0
    subseq_croissantes = {}
    subseq_croissante = []
    for i, itemset in enumerate(orderMap_Seq):
        if val <= itemset:
            val = itemset
            subseq_croissante.append(val)
        if val > itemset:
            if len(subseq_croissante) != 0:
                subseq_croissantes[(i-len(subseq_croissante),i)]=subseq_croissante
            sequences_seq_2 = orderMap_Seq[len(subseq_croissante)+1:]
            subseq_croissante = []
            val = 0
        if i == len(orderMap_Seq)-1:
            if len(subseq_croissante) != 0:
                subseq_croissantes[(i-(len(subseq_croissante)-1),i)]=subseq_croissante
    return subseq_croissantes

def select_longest_subseq_ascending(subseq_croissantes):
    subsequences = list(subseq_croissantes.values())
    len_subseq = [len(subsequences[i]) for i in range(len(subsequences))]
    return subsequences[len_subseq.index(max(len_subseq))]

        

## Total Order



def totalOrder(seq_1, seq_2, orderMap):
    subseq_croissantes = get_all_subseq_ascending(orderMap)
    longest_subseq = select_longest_subseq_ascending(subseq_croissantes)
    return (len(longest_subseq))/((len(seq_1)+len(seq_2))/2)




# POSITION ORDER



def positionOrder(seq_1, seq_2, orderMap):
    orderMap_values = [el for el in orderMap.values()]
    positionOderScore = 0
    for i, sub in enumerate(orderMap_values):
        if i == 0: continue
        sub_i = ( (sub - orderMap_values[i-1]) - ( (orderMap_values.index(sub)+1) - (orderMap_values.index(orderMap_values[i-1])+1) ) ) / ((len(seq_1)+len(seq_2))/2)
        positionOderScore += sub_i
    return positionOderScore


# ORDER SCORE



def orderScore(total_order, position_order):
    return total_order * (1 - position_order)



########## Step 3: Similarity Degree Calculation


def SimDegree(AveWeightScore, orderScore):
    sim = AveWeightScore * orderScore 
    if sim >=1:
        return 1
    else:
        return sim



########## Main SimDegree


def main_simDegree(point1, point2):
    try:
        # print(point1, point2)
        orderMap = mapping(point1, point2)
        # print(orderMap)
        AveWeightScore = GetAveWeightScore(point1, point2, orderMap)
        # print(AveWeightScore)
        total_order = totalOrder(point2, point2, orderMap)
        # print(total_order)
        position_order = positionOrder(point2, point2, orderMap)
        # print(position_order)
        order_score = orderScore(total_order, position_order)
        # print(AveWeightScore, order_score)
        return SimDegree(AveWeightScore, order_score)
    except:
        return 0


def main_distance(point1, point2):
    distance = 1 - main_simDegree(point1, point2)
    if distance <= 0:
        return 0.111
    else:
        return distance

if __name__ == '__main__':
    print(main_simDegree([{3}, {3}, {3}, {3, 38}, {43}], [{3, 38}, {43, 31}, {3, 92}]))

    



