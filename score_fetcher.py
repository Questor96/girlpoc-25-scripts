import asyncio
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


async def load_from_url(url, params=None):
    # fork behavior if _take is set
    if params.get('_take', None) is not None:
        return await _load_from_url(url, params)
    else:
        return await _load_all_from_url(url, params)


async def _load_from_url(url, params=None):
    # TODO: error handling
    if params is not None:
        url = f'{url}?params={json.dumps(params)}'
    if debug: print("url: " + url)
    response = requests.get(url)
    if response.status_code != 200:
        print(response.status_code, response.reason)
        return {}
    return response.json()


async def _load_all_from_url(url, params:dict = {}):
    data = []
    complete = False
    params['_take'] = 100
    params['_skip'] = 0
    while not complete:
        data += await _load_from_url(url, params)
        params['_skip'] += params['_take']
        if len(data) < params['_skip']: complete = True
    return data
    

async def load_data_incremental(filepath, base_api_url):
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
    new_data = await load_from_url(base_api_url, params)

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


async def load_songs():
    filepath = data_path + '/songs'
    url = 'http://api.smx.573.no/songs'
    data = await load_data_incremental(filepath, url)
    return data


async def load_charts():
    filepath = data_path + '/charts'
    url = 'http://api.smx.573.no/charts'
    data = await load_data_incremental(filepath, url)
    return data


# generic score loading
async def load_scores(params):
    url = 'http://api.smx.573.no/scores'
    data = await load_from_url(url, params)
    return data


# specific support for certain fields
async def load_player_scores(
        *,
        player_name:str,
        start:datetime = None,
        end:datetime = None,
        chart_ids:list[int] = None,
        sort_field:str = None,
        order:str = None,
        take:int = None
    ):
    params = {'gamer.username': player_name}
    if start is not None or end is not None:
        params['created_at'] = {}
    update_dict_if_not_null(params['created_at'], 'gte', str(start))
    update_dict_if_not_null(params['created_at'], 'lte', str(end))
    update_dict_if_not_null(params, 'chart.id', chart_ids)
    update_dict_if_not_null(params, '_sort', sort_field)
    update_dict_if_not_null(params, '_order', order)
    update_dict_if_not_null(params, '_take', take)
    data = await load_scores(params)
    return data


# clever idea from google genAI overview
def update_dict_if_not_null(dict, key, value):
    if value is not None:
        dict[key] = value


"""
Useful fields

songs.title, songs.subtitle - plaintext names of song

songs.id == charts.song_id

charts.id - used for looking up scores for specific charts
charts.is_enabled - check this for valid officials
charts.difficulty - block rating
"""
if __name__ == '__main__':
    # initialize event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # grab data asynchronously
    coroutines = [
        load_songs(),
        load_charts()
    ]
    [songs, charts] = loop.run_until_complete(asyncio.gather(*coroutines))
    if debug:
        print(str(len(songs)) + " songs loaded")
        print(str(len(charts)) + " charts loaded")
    

    # load event configuration
    #   pull from file eventually
    start = datetime.date(year=2024, month=11, day=1)
    end = datetime.date(year=2024, month=11, day=13)
    players = [
        "Thaya",
        "Hamaon"
    ]
    song_info = [
        {"title": "Stars", "difficulty": 24},
        {"title": "Ring the Alarm", "difficulty": 22},
        {"title": "Do My Thing", "difficulty": 20}
    ]
    num_tries_to_count = 3
    sort = 'created_at'
    order = 'asc'


    # Find chart ids based on event song_info
    # these suck lmao, how do I write them more effectively
    for song in song_info:
        for s in songs:
            if song['title'].casefold() == s['title'].casefold():
                song['id'] = s['id']
                break
    chart_ids = []
    for song in song_info:
        for chart in charts:
            if song['id'] == chart['song_id'] and song['difficulty'] == chart['difficulty']:
                chart_ids.append(chart['id'])
                break

    
    # load score data asynchronously
    coroutines = []
    for player in players:
        for chart_id in chart_ids:
            coroutines.append(
                load_player_scores(
                    player_name=player,
                    start=start,
                    end=end,
                    chart_ids=chart_id,
                    sort_field=sort,
                    order=order,
                    take=num_tries_to_count
                )
            )
    all_results = loop.run_until_complete(asyncio.gather(*coroutines))
    for result in all_results:
        for score in result:
            print(' '.join([score['gamer']['username'], score['song']['title'], str(score['score'])]))

    # clean up event loop
    loop.close()