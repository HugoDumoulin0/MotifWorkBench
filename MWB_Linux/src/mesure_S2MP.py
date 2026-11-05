#!/usr/bin/env python
# coding: utf-8

"""
S2MP variant with a maximum-weight, one-to-one, order-preserving alignment.
Original implementation: Mekki 2022.
"""

ALIGNMENT_VERSION = "ordered-dice-v1"


def weight(itemset_1, itemset_2):
    """Dice similarity between two itemsets."""
    size = len(itemset_1) + len(itemset_2)
    return 2 * len(itemset_1 & itemset_2) / size if size else 0.0


def mapping(seq_1, seq_2):
    """Align positive-weight pairs without reusing or crossing positions."""
    forward = _ordered_mapping(seq_1, seq_2)
    backward = dict(sorted((j, i) for i, j in _ordered_mapping(seq_2, seq_1).items()))
    forward_score = _alignment_score(seq_1, seq_2, forward)
    backward_score = _alignment_score(seq_1, seq_2, backward)
    if forward_score > backward_score:
        return forward
    if backward_score > forward_score:
        return backward
    # Tied scores may use a canonical orientation without affecting similarity.
    key_1 = tuple(tuple(sorted(itemset)) for itemset in seq_1)
    key_2 = tuple(tuple(sorted(itemset)) for itemset in seq_2)
    return backward if key_1 > key_2 else forward


def _ordered_mapping(seq_1, seq_2):
    rows, cols = len(seq_1), len(seq_2)
    scores = [[(0.0, 0, 0)] * (cols + 1) for _ in range(rows + 1)]
    moves = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            best = scores[i - 1][j]
            move = 1
            if scores[i][j - 1] > best:
                best, move = scores[i][j - 1], 2
            pair_weight = weight(seq_1[i - 1], seq_2[j - 1])
            if pair_weight > 0:
                previous = scores[i - 1][j - 1]
                # Maximize weight, then coverage, then prefer nearby positions.
                paired = (
                    previous[0] + pair_weight,
                    previous[1] + 1,
                    previous[2] - abs(i - j),
                )
                if paired >= best:
                    best, move = paired, 3
            scores[i][j], moves[i][j] = best, move

    pairs = []
    i, j = rows, cols
    while i and j:
        move = moves[i][j]
        if move == 3:
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif move == 1:
            i -= 1
        else:
            j -= 1
    return dict(reversed(pairs))


def GetAveWeightScore(seq_1, seq_2, orderMap):
    if not orderMap:
        return 0.0
    return sum(weight(seq_1[i], seq_2[j]) for i, j in orderMap.items()) / len(orderMap)


def totalOrder(seq_1, seq_2, orderMap):
    # Every pair in mapping() belongs to the same increasing subsequence.
    mean_length = (len(seq_1) + len(seq_2)) / 2
    return len(orderMap) / mean_length if mean_length else 0.0


def positionOrder(seq_1, seq_2, orderMap):
    mean_length = (len(seq_1) + len(seq_2)) / 2
    if not mean_length:
        return 0.0
    pairs = sorted(orderMap.items())
    gap_difference = sum(
        abs((j - previous_j) - (i - previous_i))
        for (previous_i, previous_j), (i, j) in zip(pairs, pairs[1:])
    )
    return gap_difference / mean_length


def orderScore(total_order, position_order):
    return total_order * max(0.0, 1 - position_order)


def SimDegree(AveWeightScore, orderScore):
    return max(0.0, min(1.0, AveWeightScore * orderScore))


def _alignment_score(point1, point2, orderMap):
    if not orderMap:
        return 0.0
    average_weight = GetAveWeightScore(point1, point2, orderMap)
    total_order = totalOrder(point1, point2, orderMap)
    position_order = positionOrder(point1, point2, orderMap)
    return SimDegree(average_weight, orderScore(total_order, position_order))


def main_simDegree(point1, point2):
    return _alignment_score(point1, point2, mapping(point1, point2))


def main_distance(point1, point2):
    distance = 1 - main_simDegree(point1, point2)
    if distance <= 0:
        return 0.111
    return distance


if __name__ == "__main__":
    print(main_simDegree([{3}, {3}, {3}, {3, 38}, {43}], [{3, 38}, {43, 31}, {3, 92}]))
