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
    event_folder = './girlpoc-25-group/'
    gs = gspread_auth()
    rs = gs.open_by_key(load_from_json(event_folder + 'group_results_spreadsheet_key.json').get('key'))
    
    m1_json = load_from_json(event_folder + 'match_1.json')
    m1_config = m1_json['config']
    m1_charts = m1_json['charts']
    m1_entrants = load_from_json(event_folder + 'entrants_1.json')
    m1 = GauntletTournament(
        name="Match 1",
        start_date=m1_config['start_date'],
        end_date=m1_config['end_date'],
        attempts_to_count=m1_config['attempts_to_count'],
    )
    m1.filter_songs_and_charts(m1_charts)
    m1.load_entrants(m1_entrants)
    m1.get_all_scores()
    m1.report_results(rs.worksheet("Match 1"))

    m2_json = load_from_json(event_folder + 'match_2.json')
    m2_config = m2_json['config']
    m2_charts = m2_json['charts']
    m2_entrants = load_from_json(event_folder + 'entrants_2.json')
    m2 = GauntletTournament(
        name="Match 2",
        start_date=m2_config['start_date'],
        end_date=m2_config['end_date'],
        attempts_to_count=m2_config['attempts_to_count'],
    )
    m2.filter_songs_and_charts(m2_charts)
    m2.load_entrants(m2_entrants)
    m2.get_all_scores()
    m2.report_results(rs.worksheet("Match 2"))