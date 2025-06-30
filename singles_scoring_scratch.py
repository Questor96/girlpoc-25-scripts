import pandas as pd
import pprint

def score_calc(index, max_index):
    x = index / max_index
    y = -0.675 * pow(x,3) + 1.8000000001575* pow(x,2) + -2.0250000001575*x + 1
    y *= 10  # adjust to [10,1] from [1, 0.1]
    return y

def process_scores(tsv):
    scores = pd.read_csv(tsv, sep="\t")

    total_scores = {}
    df = scores[scores['Eligible for Ranking'] == True]
    df = df.reset_index(drop=True)
    for i in range(2, 11):
        song_df = df.iloc[:, [0, i]].sort_values(by=df.columns[i], ascending=False).reset_index(drop=True)
        for i in range(len(song_df)):
            entrant = song_df.loc[i, song_df.columns[0]]
            score = song_df.loc[i, song_df.columns[1]]
            if score == 0:
                score_val = 0
            else:
                score_val = score_calc(i, len(song_df) - 1)
            try:
                total_scores[entrant] += score_val
            except KeyError:
                total_scores[entrant] = score_val
    return dict(sorted(total_scores.items(), key=lambda item: item[1], reverse=True))

def write_dict(file, my_dict):
    for i, j in my_dict.items():
        file.write(f"{i}\t{round(j, 1)}\n")

if __name__ == "__main__":
    with open('girlpoc-25-singles/final_results.tsv', "w") as file:
        file.write("Hard\n")
        write_dict(file, process_scores('girlpoc-25-singles/hard_scores.tsv'))
        file.write("\nIntro to Wild\n")
        write_dict(file, process_scores('girlpoc-25-singles/intro_wild_scores.tsv'))
        file.write("\nWild\n")
        write_dict(file, process_scores('girlpoc-25-singles/wild_scores.tsv'))