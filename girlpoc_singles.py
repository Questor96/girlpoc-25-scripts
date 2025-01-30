import json

from gcs.gspread_auth import gspread_auth
from src.Tournament import GauntletTournament

debug = False

# utilities
def load_from_json(path):
    with open(path) as file:
        return json.load(file)


if __name__ == "__main__":
    # cross-event constants
    event_folder = './girlpoc-25-singles/'
    gs = gspread_auth()
    rs = gs.open_by_key(load_from_json(event_folder + 'singles_results_spreadsheet_key.json').get('key'))
    players = load_from_json(event_folder + 'players.json')


    hard_json = load_from_json(event_folder + 'hard.json')
    hard_config = hard_json['config']
    hard_charts = hard_json['charts']
    ht = GauntletTournament(
        name="Hard",
        start_date=hard_config['start_date'],
        end_date=hard_config['end_date'],
        attempts_to_count=hard_config['attempts_to_count'],
        ineligible_difficulty=hard_config['disqualify_if']['difficulty'],
        ineligible_score=hard_config['disqualify_if']['score_gte'],
        ineligible_count=hard_config['disqualify_if']['count']
    )
    ht.load_charts(hard_charts)
    ht.load_players(players)
    ht.get_all_scores()
    ht.report_results(rs.worksheet("Hard"))

    iwt_json = load_from_json(event_folder + 'intro_wild.json')
    iwt_config = iwt_json['config']
    iwt_charts = iwt_json['charts']
    iwt = GauntletTournament(
        name="Intro to Wild",
        start_date=iwt_config['start_date'],
        end_date=iwt_config['end_date'],
        attempts_to_count=iwt_config['attempts_to_count'],
        ineligible_difficulty=iwt_config['disqualify_if']['difficulty'],
        ineligible_score=iwt_config['disqualify_if']['score_gte'],
        ineligible_count=iwt_config['disqualify_if']['count']
    )
    iwt.load_charts(iwt_charts)
    iwt.load_players(players)
    iwt.get_all_scores()
    iwt.report_results(rs.worksheet("Intro to Wild"))

    w_json = load_from_json(event_folder + 'wild.json')
    w_config = w_json['config']
    w_charts = w_json['charts']
    wt = GauntletTournament(
        name="Wild",
        start_date=w_config['start_date'],
        end_date=w_config['end_date'],
        attempts_to_count=w_config['attempts_to_count']
    )
    wt.load_charts(w_charts)
    wt.load_players(players)
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
