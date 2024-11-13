import requests
import datetime
import pprint

# lazy printer for debugging:)
debug = True
pp = pprint.PrettyPrinter(indent=2)


def load_from_url(url):
    # TODO: error handling
    response = requests.get(url)
    if response.status_code != 200:
        print(response.status_code, response.reason)
        return {}
    return response.json()

# retrieve song library
def load_songs():
    # TODO: check for latest version?
    url = 'http://smx.573.no/api/songs'
    song_library_dict = load_from_url(url)
    
    if debug:
        pp.pprint([x for x in song_library_dict if str(x['title']).lower() == "Definition of a Badboy".lower()])
    # TODO: store to file?
    return song_library_dict

# retrieve chart library
def load_charts():
    # TODO: check for latest version?
    url = 'http://smx.573.no/api/charts'
    chart_library_dict = load_from_url(url)
    
    if debug:
        pp.pprint([x for x in chart_library_dict if x['song_id'] == 618])
    # TODO: store to file
    return chart_library_dict

"""
Useful fields

songs.title, songs.subtitle - plaintext names of song

songs.id == charts.song_id

charts.id - used for looking up scores for specific charts
charts.is_enabled - check this for valid officials
charts.difficulty - block rating
"""
if __name__ == '__main__':
    charts = load_charts()
    songs = load_songs()

    song_names = [
        "Definition of a Badboy"
    ]
    song_names = [x.lower() for x in song_names]
    song_ids = [x['id'] for x in songs if str(x['title']).lower() in song_names]

    start = datetime.date(year=2024, month=11, day=1)
    end = datetime.date(year=2024, month=11, day=13)
    player = "thaya"
    chart_ids = [str(x['id']) for x in charts if x['song_id'] in song_ids]
    num_tries_to_count = 3
    player_scores_url = f'http://smx.573.no/api/scores?from={start}&to={end}&user={player}&chart_ids={','.join(chart_ids)}&asc=1'
    print(player_scores_url)
    player_scores = load_from_url(player_scores_url)
    trunc_player_scores = player_scores[:num_tries_to_count]
    pp.pprint([_['score'] for _ in trunc_player_scores])