import json

from gcs.gspread_auth import gspread_auth
from src.Tournament import LadderTournament

debug = False

# utilities
def load_from_json(path):
    with open(path) as file:
        return json.load(file)

if __name__ == "__main__":
    event_folder = "./girlpoc-25-ladder/"
    #gs = gspread_auth()
    #rs = gs.open_by_key(load_from_json(event_folder + "ladder_results_spreadsheet_key.json").get("key"))
    entrants = load_from_json(event_folder + "entrants.json")

    #config = load_from_json(event_folder + "config.json")

    lt = LadderTournament(
        name="Girlpoc 2025.5",
        start_date="2025-06-26",
        end_date="2025-06-30",
        ladder_point_scalar=1.2
    )
    lt.load_entrants(entrants)
    lt.get_all_scores()

    for entrant in lt.entrants:
        print(f"{entrant.name=}")
        for score in entrant.scores:
            print(
                f"title={score.song.title} "
                f"difficulty={score.chart.difficulty} "
                f"score={score.score} "
                f"ladder={score.ladder_points(lt.ladder_point_scalar)} "
            )
        print("")