from pathlib import Path

from gcs.gspread_auth import gspread_auth
from src.Tournament import (
    GauntletTournament,
    LadderTournament,
    make_eligibility_spreadsheet_for_gauntlet_tournaments,
)
from src.helpers import load_config_file


DEBUG = False

# Event configuration details
EVENT_FOLDER = Path(__file__).parent / "girlpoc-jan-26"
ENTRANTS_CONFIG_FILENAME = "entrants.yaml"
SPREADSHEET_CONFIG = "result_spreadsheet_key.yaml"
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
        GauntletTournament.from_config_file(
            config_filepath=EVENT_FOLDER / event_config_filename,
            entrant_filepath=EVENT_FOLDER / ENTRANTS_CONFIG_FILENAME,
        )
        for event_config_filename in GAUNTLET_CONFIGS
    ]
    if gts:
        make_eligibility_spreadsheet_for_gauntlet_tournaments(
            result_spreadsheet=result_spreadsheet,
            tournaments=gts,
        )
    lts = [
        LadderTournament.from_config_file(
            config_filepath=EVENT_FOLDER / event_config_filename,
            entrant_filepath=EVENT_FOLDER / ENTRANTS_CONFIG_FILENAME,
        )for event_config_filename in LADDER_CONFIGS
    ]
    for tournament in gts + lts:
        tournament.run(result_spreadsheet)
