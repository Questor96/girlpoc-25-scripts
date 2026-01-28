import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any

import gspread_formatting as gsf
from gspread.cell import Cell
from gspread.spreadsheet import Spreadsheet

from src.Eligibility import EligibilityConfig
from src.Tournament import Tournament, GauntletTournament, LadderTournament


# Config Loading
def load_config_file(path: Path) -> Any:
    if path.suffix == '.yaml':
        return _load_from_yaml(path)
    if path.suffix == '.json':
        return _load_from_json(path)
    else:
        raise NotImplementedError(f"{path.suffix} filetype not yet supported")

def _load_from_json(path) -> Any:
    with open(path) as file:
        return json.load(file)

def _load_from_yaml(path) -> Any:
    with open(path) as file:
        return yaml.safe_load(file)


# Bad Factories
def make_gauntlet_tournament_from_config(
    event_folder: Path,
    event_config_filename: str,
    entrants_config_filename: str,
) -> GauntletTournament:
    # Load base config
    base_dict: dict = load_config_file(event_folder / event_config_filename)
    config: dict = base_dict["config"]
    
    # create GauntletTournament
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
        start_date=datetime.fromisoformat(str(config["start_date"])),
        end_date=datetime.fromisoformat(str(config["end_date"])),
        attempts_to_count=config["attempts_to_count"],
        ineligible_requirements=eligibility_config,
    )

    # do chart and entrant initialization
    charts: list[dict] = base_dict["charts"]
    tournament.filter_songs_and_charts(charts)
    entrants: list = load_config_file(event_folder / entrants_config_filename)
    tournament.load_entrants(entrants)
    return tournament

def make_ladder_tournament_from_config(
    event_folder: Path,
    event_config_filename: str,
    entrants_config_filename: str,
):
    config: dict = load_config_file(event_folder / event_config_filename)
    tournament = LadderTournament(
        name = "Full",
        start_date=config["start_date"],
        end_date=config["end_date"],
        scoring_floor=config["scoring_floor"],
        ladder_point_scalar=config["ladder_point_scalar"],
        num_scores_to_count=config["num_scores_to_count"],
        overall_results_sheet_name=config["overall_results_sheet_name"],
        score_details_sheet_name=config["score_details_sheet_name"],
        restrict_to_difficulty_name=config["restrict_to_difficulty_name"],
    )
    entrants: list = load_config_file(event_folder / entrants_config_filename)
    tournament.load_entrants(entrants)
    return tournament


# print info about multiple tournament eligibilities
def make_eligibility_spreadsheet_for_gauntlet_tournaments(
    result_spreadsheet: Spreadsheet,
    tournaments: list[Tournament],
    worksheet_name: str = "Bracket Eligibility",
):
    worksheet = result_spreadsheet.worksheet(worksheet_name)
    cells = []
    col = 1
    row = 2
    for entrant in tournaments[0].entrants:  # player names
        cells.append(Cell(row, col, entrant.name))
        row += 1
    col = 2
    for tournament in tournaments:  # tournament eligibilities
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
            format=gsf.CellFormat(
                textFormat=gsf.TextFormat(bold=True),
                backgroundColor=gsf.Color.fromHex("#e67c73")
            ),
        ),
    )
    green_rule = gsf.ConditionalFormatRule(
        ranges=[gsf.GridRange.from_a1_range('A1:F2000', worksheet)],
        booleanRule=gsf.BooleanRule(
            condition=gsf.BooleanCondition('TEXT_EQ', [str(True)]),
            format=gsf.CellFormat(
                textFormat=gsf.TextFormat(bold=True),
                backgroundColor=gsf.Color.fromHex("#57bb8a"),
            ),
        ),
    )
    rules = gsf.get_conditional_format_rules(worksheet)
    rules.clear()
    rules.append(red_rule)
    rules.append(green_rule)
    rules.save()
    gsf.set_frozen(worksheet, rows=1, cols=1)