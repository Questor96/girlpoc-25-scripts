import json
from pathlib import Path
from typing import Any

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
    spreadsheet_info: dict[str, str] = load_from_json(event_folder / "result_spreadsheet_key.json")
    entrants: list[str] = load_from_json(event_folder / "entrants.json")
    hard_config: dict[str, int | str] = load_from_json(event_folder / "hard.json")

    #result_spreadsheet = gs.open_by_key(spreadsheet_info["key"])

    hard_tournament = GauntletTournament(
        name="Jan '26 Hard",
        start_date="2025-12-01",
        end_date="2026-01-01",
        attempts_to_count=3,
        ineligible_difficulty=21,
        ineligible_score=99000,
        ineligible_count=3,
    )
    hard_tournament.load_entrants(entrants)
    hard_tournament.get_all_scores()
    #hard_tournament.report_results(result_spreadsheet.worksheet("Hard"))