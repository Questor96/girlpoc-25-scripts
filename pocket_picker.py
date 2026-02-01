from src.ScoreFetcher import ScoreFetcher
import datetime
import json

debug = False

if __name__ == '__main__':
    debug = True
    # set difficulty, block window, time range
    config = {
        "difficulty_name": "wild",
        "difficulty": [20,21,22,23],
        "start": datetime.datetime.now() - datetime.timedelta(weeks=8)
    }
    # set entrant to compute pick for
    target = "Hamaon"
    # set opponents
    entrants = [
        target,
        "Pilot",
        "JellySlosh",
        "Thaya"
    ]
    #get score info for entrant, opponents
    sf = ScoreFetcher(debug=True)

    requests = [
        sf.load_entrant_scores(
            entrant_name=entrant,
            start=config["start"],
            difficulty=config["difficulty"],
            difficulty_names=config["difficulty_name"],
            sort_field="created_at",
            order="asc",
        )
        for entrant in entrants
    ]
    results = sf.execute_coroutines(requests)

    with open('test_results.json', 'w') as out_file:
        json.dump(results,out_file)
