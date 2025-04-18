import pandas as pd
from itertools import product

TWO_PLAYER_OPTIONS = set([choice for choice in list(product([0,0,0,1,1,1], repeat=6)) if choice.count(1) == 3 and choice.count(0) == 3])
THREE_PLAYER_OPTIONS = set([choice for choice in list(product([0,0,1,1,2,2], repeat=6)) if choice.count(2) == 2 and choice.count(1) == 2 and choice.count(0) == 2])

def compute_max_combo(scores, two_player: bool = False):
    options = THREE_PLAYER_OPTIONS
    if two_player:
        options = TWO_PLAYER_OPTIONS
    max_score = 0
    best_option = []
    for option in options:
        index = 0
        total = 0
        for val in option:
            total += scores[val][index]
        if total > max_score:
            max_score = total
            best_option = option
    return max_score, best_option

print("\tMatch 1")
t1 = ["MarryCherry", "freyja", "Pyrona"]
t1_scores = [
    [99581, 99751, 98831, 96691, 99343, 99885],
    [99521, 99800, 93974, 99288, 99561, 99506],
    [91636, 96245, 91635, 80143, 98452, 97048]
]
print(t1)
print(compute_max_combo(t1_scores))
print("alt, excluding Pyrona: ", compute_max_combo(t1_scores, True))

t2 = ["NabiChou", "MeGoesMoo", "DIGI"]
t2_scores = [
    [98877, 99464, 98655, 95900, 99285, 98456],
    [99450, 99327, 98559, 97762, 98615, 99303],
    [91082, 82595, 0, 0, 84161, 93843]
]
print(t2)
print(compute_max_combo(t2_scores))

print("\n\n\tMatch 2")

t3 = ["EMCAT", "Hamaon", "CTEMI"]
t3_scores = [
    [99674, 99974, 99691, 99846, 99880, 99970],
    [97966, 99773, 99555, 99477, 99675, 99670],
    [97046, 99549, 98806, 99640, 99820, 99707]
]
print(t3)
print(compute_max_combo(t3_scores))

t4 = ["mxl100", "Lenni", "ZephyrNoBar"]
t4_scores = [
    [97560, 99723, 99292, 99431, 99850, 99816],
    [98134, 0, 99601, 99753, 99582, 99970],
    [97516, 99747, 99072, 99105, 99759, 98980]
]
print(t4)
print(compute_max_combo(t4_scores))