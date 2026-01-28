from pathlib import Path

from gcs.gspread_auth import gspread_auth
from src.helpers import (
    load_config_file,
    make_eligibility_spreadsheet_for_gauntlet_tournaments,
    make_gauntlet_tournament_from_config,
    make_ladder_tournament_from_config,
)


DEBUG = False

# Event configuration details
EVENT_FOLDER = Path(__file__).parent / "girlpoc-jan-26"
ENTRANTS_CONFIG_FILENAME = "entrants.yaml"
SPREADSHEET_CONFIG = "result_spreadsheet.yaml"
GAUNTLET_CONFIGS = [
    "hard.yaml",
    "hard-plus.yaml",
    "intro-wild.yaml",
    "wild.yaml",
    "wild-plus.yaml",
]
LADDER_CONFIGS = ["full.yaml"]


if __name__ == "__main__":
    gs = gspread_auth()
    spreadsheet_key: str = load_config_file(EVENT_FOLDER / SPREADSHEET_CONFIG)["key"]
    result_spreadsheet = gs.open_by_key(spreadsheet_key)

    gts = [
        make_gauntlet_tournament_from_config(EVENT_FOLDER, event_config_filename, ENTRANTS_CONFIG_FILENAME)
        for event_config_filename in GAUNTLET_CONFIGS
    ]
    make_eligibility_spreadsheet_for_gauntlet_tournaments(
        result_spreadsheet=result_spreadsheet,
        tournaments=gts,
    )
    lts = [
        make_ladder_tournament_from_config(EVENT_FOLDER, event_config_filename, ENTRANTS_CONFIG_FILENAME)
        for event_config_filename in LADDER_CONFIGS
    ]
    for tournament in gts + lts:
        tournament.run(result_spreadsheet)