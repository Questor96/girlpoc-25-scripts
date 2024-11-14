import requests
import datetime
import json
import pprint
from urllib.parse import urlencode

# file store info
config_path = './config'
data_path = './data'

# lazy printer for debugging:)
debug = True
pp = pprint.PrettyPrinter(indent=2)


def load_from_url(url, params=None):
    # TODO: error handling
    if params is not None:
        url = f'{url}?params={json.dumps(params)}'
    if debug: print("url: " + url)
    response = requests.get(url)
    if response.status_code != 200:
        print(response.status_code, response.reason)
        return {}
    return response.json()


def load_all_from_url(url, params:dict = {}):
    # TODO: error handling
    data = []
    complete = False
    params['_take'] = 100
    params['_skip'] = 0
    while not complete:
        data += load_from_url(url, params)
        params['_skip'] += params['_take']
        if len(data) < params['_skip']: complete = True
    return data
    

def load_data_incremental(filepath, base_api_url):
    time_fmt = "%a, %b %d %Y %H:%M:%S"
    upd_at_filepath = filepath + '_updated_at.txt'
    data_filepath = filepath + '_data.json'
    
    # get previous timestamp from file
    try:
        with open(upd_at_filepath, 'r') as upd_file:
            prev_upd_at = datetime.datetime.strptime(upd_file.read(), time_fmt)
            previous_search = True
    except FileNotFoundError:
        previous_search = False
    
    # get existing data from file
    try:
        with open(data_filepath, "r") as data_file:
            data: list = json.load(data_file)
    except FileNotFoundError:
        data: list = []
    
    # grab current timestamp before beginning data operations
    curr_time = datetime.datetime.now()
    
    # query API for data updated since previous timestamp
    params = {}
    if previous_search:
        params = {"updated_at": {"gt": str(prev_upd_at)}}
    new_data = load_all_from_url(base_api_url, params)

    # merge new data into existing
    ids_to_update = [entry['id'] for entry in new_data]
    data = [entry for entry in data if entry['id'] not in ids_to_update]
    for entry in new_data:
        data.append(entry)

    # save data to file
    with open(data_filepath, "w") as data_file:
        json.dump(data, data_file)
    
    # save timestamp to file
    with open(upd_at_filepath, "w") as upd_file:
        upd_file.write(datetime.datetime.strftime(curr_time, time_fmt))

    return data


def load_songs():
    filepath = data_path + '/songs'
    url = 'http://api.smx.573.no/songs'
    data = load_data_incremental(filepath, url)
    return data


def load_charts():
    filepath = data_path + '/charts'
    url = 'http://api.smx.573.no/charts'
    data = load_data_incremental(filepath, url)
    return data


"""
Useful fields

songs.title, songs.subtitle - plaintext names of song

songs.id == charts.song_id

charts.id - used for looking up scores for specific charts
charts.is_enabled - check this for valid officials
charts.difficulty - block rating
"""
if __name__ == '__main__':
    songs = load_songs()
    print(str(len(songs)) + " songs loaded")
    charts = load_charts()
    print(str(len(charts)) + " charts loaded")

    song_names = [
        "Definition of a Badboy"
    ]
    song_names = [x.lower() for x in song_names]
    song_ids = [x['id'] for x in songs if str(x['title']).lower() in song_names]

    start = datetime.date(year=2024, month=11, day=1)
    end = datetime.date(year=2024, month=11, day=13)
    player = "Thaya"
    chart_ids = [x['id'] for x in charts if x['song_id'] in song_ids]
    num_tries_to_count = 3

    player_scores_url = 'http://api.smx.573.no/scores'
    query_params = {
        '_order': 'asc',
        '_sort': "created_at",
        'gamer.username': player,
        'chart.id': chart_ids,
        'created_at': {
            "gt": str(start),
            "lte": str(end)
        }
    }
    player_scores = load_from_url(player_scores_url, query_params)
    pp.pprint([_['score'] for _ in player_scores][:num_tries_to_count])