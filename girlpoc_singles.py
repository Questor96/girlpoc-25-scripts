import json

from gcs.gspread_auth import gspread_auth
from src.Tournament import GauntletTournament

debug = False

# utilities
def load_from_json(path):
    with open(path) as file:
        return json.load(file)


if __name__ == "__main__":
    event_folder = './girlpoc-25-singles/'
    config = load_from_json(event_folder + 'config.json')
    gs = gspread_auth()
    rs = gs.open_by_key(load_from_json(event_folder + 'singles_results_spreadsheet_key.json').get('key'))

    ht = GauntletTournament(
        name="Hard",
        start_date=config['start_date'],
        end_date=config['end_date'],
        attempts_to_count=config['attempts_to_count'],
        ineligible_difficulty=18,
        ineligible_score=99000
    )
    ht.load_charts(load_from_json(event_folder + 'hard.json'))
    ht.load_players(load_from_json(event_folder + 'players.json'))
    ht.get_all_scores()
    ht.report_results(rs.worksheet("Hard"))

    iwt = GauntletTournament(
        name="Intro to Wild",
        start_date=config['start_date'],
        end_date=config['end_date'],
        attempts_to_count=config['attempts_to_count'],
        ineligible_difficulty=21,
        ineligible_score=99000
    )
    iwt.load_charts(load_from_json(event_folder + 'intro_wild.json'))
    iwt.load_players(load_from_json(event_folder + 'players.json'))
    iwt.get_all_scores()
    iwt.report_results(rs.worksheet("Intro to Wild"))

    wt = GauntletTournament(
        name="Wild",
        start_date=config['start_date'],
        end_date=config['end_date'],
        attempts_to_count=config['attempts_to_count']
    )
    wt.load_charts(load_from_json(event_folder + 'wild.json'))
    wt.load_players(load_from_json(event_folder + 'players.json'))
    wt.get_all_scores()
    wt.report_results(rs.worksheet("Wild"))

    if debug:
        tournaments = [ht, iwt, wt]
        for tournament in tournaments:
            print(tournament.name)
            for player in tournament.players:
                for score in player.scores:
                    print("\t".join([player.name, score.chart.song_title, score.value]))
                print()
