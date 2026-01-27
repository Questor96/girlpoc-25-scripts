import json
from pathlib import Path
from typing import Any
from datetime import datetime

import gspread_formatting as gsf
from gspread.client import Client as GSClient
from gspread.cell import Cell
from gspread.spreadsheet import Spreadsheet

from gcs.gspread_auth import gspread_auth
from src.Tournament import GauntletTournament
from src.Eligibility import EligibilityConfig

debug = False

# utilities
def load_from_json(path) -> Any:
    with open(path) as file:
        return json.load(file)

def make_gauntlet_tournament_from_json(
    event_folder: Path,
    event_json_name: str,
) -> GauntletTournament:
    entrants: list = load_from_json(event_folder / "entrants.json")
    base_json: dict = load_from_json(event_folder / event_json_name)
    config: dict = base_json["config"]
    charts: list[dict] = base_json["charts"]
    eligibility_json = config.get("disqualify_if")
    event_name = config.get("name", "unknown tournament")
    if eligibility_json:
        eligibility_config = [
            EligibilityConfig(
                score=requirement["score_gte"],
                difficulty=requirement["difficulty"],
                count=requirement["count"],
            )
            for requirement in config["disqualify_if"]
        ]
    else:
        eligibility_config = None
    tournament = GauntletTournament(
        name=event_name,
        start_date=datetime.fromisoformat(config["start_date"]),
        end_date=datetime.fromisoformat(config["end_date"]),
        attempts_to_count=config["attempts_to_count"],
        ineligible_requirements=eligibility_config,
    )
    # do chart and entrant initialization
    tournament.filter_songs_and_charts(charts)
    tournament.load_entrants(entrants)
    return tournament

def run_gauntlet_tournament(
    tournament: GauntletTournament,
    result_spreadsheet: Spreadsheet
):
    tournament.get_all_scores()
    tournament.report_results(result_spreadsheet.worksheet(tournament.name))

def make_eligibility_spreadsheet(
    gspread_client: GSClient,
    tournaments: list[GauntletTournament],
):
    spreadsheet_info: dict = load_from_json(event_folder / "eligibility_spreadsheet_key.json")
    result_spreadsheet = gspread_client.open_by_key(spreadsheet_info["key"])
    worksheet = result_spreadsheet.worksheet("Bracket Eligibility")
    cells = []
    # player names
    # column 1 always for player names
    # assumes players are in same order in all tournaments
    col = 1
    row = 2
    for entrant in tournaments[0].entrants:
        cells.append(Cell(row, col, entrant.name))
        row += 1

    # tournament eligibilities
    col = 2
    for tournament in tournaments:
        row = 1
        cells.append(Cell(row, col, tournament.name))
        row += 1
        for entrant in tournament.entrants:
            cells.append(Cell(row, col, str(entrant.can_compete)))
            row += 1
        col += 1

    worksheet.update_cells(cells)
    
    # conditional formatting
    red_rule = gsf.ConditionalFormatRule(
        ranges=[gsf.GridRange.from_a1_range('A1:F2000', worksheet)],
        booleanRule=gsf.BooleanRule(
            condition=gsf.BooleanCondition('TEXT_EQ', [str(False)]),
            format=gsf.CellFormat(textFormat=gsf.TextFormat(bold=True), backgroundColor=gsf.Color(1,0,0))
        )
    )
    green_rule = gsf.ConditionalFormatRule(
        ranges=[gsf.GridRange.from_a1_range('A1:F2000', worksheet)],
        booleanRule=gsf.BooleanRule(
            condition=gsf.BooleanCondition('TEXT_EQ', [str(True)]),
            format=gsf.CellFormat(textFormat=gsf.TextFormat(bold=True), backgroundColor=gsf.Color(0,1,0))
        )
    )
    rules = gsf.get_conditional_format_rules(worksheet)
    rules.clear()
    rules.append(red_rule)
    rules.append(green_rule)
    rules.save()


if __name__ == "__main__":
    event_folder = Path("./girlpoc-jan-26")
    gs = gspread_auth()
    spreadsheet_info: dict = load_from_json(event_folder / "result_spreadsheet_key.json")
    result_spreadsheet = gs.open_by_key(spreadsheet_info["key"])

    event_jsons = [
        "hard.json",
        "hard-plus.json",
        "intro-wild.json",
        "wild.json",
        "wild-plus.json",
    ]
    tournaments = [
        make_gauntlet_tournament_from_json(event_folder, event_json)
        for event_json in event_jsons
    ]
    make_eligibility_spreadsheet(
        gspread_client=gs,
        tournaments=tournaments,
    )
    for tournament in tournaments:
        run_gauntlet_tournament(tournament, result_spreadsheet)