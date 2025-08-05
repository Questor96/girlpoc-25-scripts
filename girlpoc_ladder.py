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
    gs = gspread_auth()
    result_spreadsheet = gs.open_by_key(load_from_json(event_folder + "ladder_results_spreadsheet_key.json").get("key"))
    entrants = load_from_json(event_folder + "entrants.json")
    config = load_from_json(event_folder + "config.json")

    lt = LadderTournament(
        name="Girlpoc 2025.5",
        start_date=config["start_date"],
        end_date=config["end_date"],
        scoring_floor=config["scoring_floor"],
        ladder_point_scalar=config["ladder_point_scalar"],
        num_songs_to_count=config["num_songs_to_count"],
    )
    lt.load_entrants(entrants)
    lt.get_all_scores()
    lt.report_results(
        spreadsheet=result_spreadsheet,
        overall_results_sheet_name="Summary",
        detail_results_sheet_name="Details"
    )
