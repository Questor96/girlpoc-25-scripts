import json
from pathlib import Path
from typing import Any
from datetime import datetime

from gcs.gspread_auth import gspread_auth
from src.Tournament import GauntletTournament

debug = False

# utilities
def load_from_json(path) -> Any:
    with open(path) as file:
        return json.load(file)

if __name__ == "__main__":
    event_folder = Path("./girlpoc-jan-26")
    gs = gspread_auth()
    spreadsheet_info: dict = load_from_json(event_folder / "result_spreadsheet_key.json")
    entrants: list = load_from_json(event_folder / "entrants.json")
    hard_json: dict = load_from_json(event_folder / "hard.json")
    
    result_spreadsheet = gs.open_by_key(spreadsheet_info["key"])

    hard_config: dict = hard_json["config"]
    hard_charts: list[dict] = hard_json["charts"]
    hard_tournament = GauntletTournament(
        name="Jan '26 Hard",
        start_date=datetime.fromisoformat("2024-12-01"),
        end_date=datetime.fromisoformat("2026-01-01"),
        attempts_to_count=3,
        ineligible_difficulty=21,
        ineligible_score=99000,
        ineligible_count=3,
    )
    hard_tournament.filter_songs_and_charts(hard_charts)
    hard_tournament.load_entrants(entrants)
    hard_tournament.get_all_scores()
    hard_tournament.report_results(result_spreadsheet.worksheet("Hard"))