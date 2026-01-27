import asyncio
import aiohttp
from datetime import datetime
import json
import pprint

from src.Chart import Chart
from src.Gamer import Gamer
from src.Score import Score
from src.Song import Song

# lazy printer for debugging:)
pp = pprint.PrettyPrinter(indent=2)

class ScoreFetcher():

    def __init__(self, *, debug: bool=False):
        self.config_path = './config'
        self.data_path = './data'
        self.songs: list[Song] = []
        self.charts: list[Chart] = []
        self.debug = debug

        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)
        self._session: aiohttp.ClientSession = None
        self._init_songs_and_charts()

    def __del__(self):
        self._event_loop.close()

    def _init_songs_and_charts(self):
        coroutines = [
            self.load_songs(),
            self.load_charts(),
        ]
        [self.songs, self.charts] = self._event_loop.run_until_complete(self.run_tasks_in_aiohttp_client(coroutines))
        if self.debug:
            print(str(len(self.songs)) + " songs loaded")
            print(str(len(self.charts)) + " charts loaded")

    async def run_tasks_in_aiohttp_client(self, coroutines):
        """
        runs set of async coroutines w/ a aiohttp session
        session is peeked at from actual point of access, not passed along stack
        so it's invisible to usage.
        Pattern of usage -> results = event_loop.run_until_complete(run_tasks_in_aiohttp_client(coroutines))
        """
        results = []
        async with aiohttp.ClientSession() as session:
            self._session = session
            for coroutine in coroutines:
                result = await coroutine
                results.append(result)
        self._session = None
        return results

    async def _load_from_url(self, url, params=None):
        # TODO: error handling
        # grab active session from instance variable
        session: aiohttp.ClientSession = self._session
        if params is not None:
            if self.debug:
                pp.pprint(params)
            url = f'{url}?params={json.dumps(params)}'
        if self.debug:
            print("url: " + url)
        response = await session.request('GET', url=url)
        if response.status != 200:
            print(url, response.status, response.reason)
            return {}
        data = await response.json()
        return data

    async def load_from_url(self, url: str, params: dict = {}):
        data = []
        complete = False
        initial_take = params.get('_take', None)
        params['_take'] = initial_take if initial_take is not None and initial_take < 100 else 100  # max _take of 100, per API spec
        params['_skip'] = 0
        while not complete:
            # grab next set of data
            data += await self._load_from_url(url, params)
            # update count of records searched
            params['_skip'] += params['_take']
            
            # update take param to not excede initial_take, if necessary
            if initial_take is not None:
                params['_take'] = min(initial_take - params['_skip'], 100)

            # exit conditions
            if len(data) < params['_skip']:  # reached end of data, quit
                complete = True
            if len(data) == initial_take:  # reached requisite # of entries, quit
                complete = True
            
        return data

    async def load_data_incremental(self, filepath, base_api_url):
        time_fmt = "%a, %b %d %Y %H:%M:%S"
        upd_at_filepath = filepath + '_updated_at.txt'
        data_filepath = filepath + '_data.json'
        
        # get previous timestamp from file
        try:
            with open(upd_at_filepath, 'r') as upd_file:
                prev_upd_at = datetime.strptime(upd_file.read(), time_fmt)
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
        curr_time = datetime.now()
        
        # query API for data updated since previous timestamp
        params = {}
        if previous_search:
            params = {"updated_at": {"gt": str(prev_upd_at)}}
        new_data = await self.load_from_url(base_api_url, params)

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
            upd_file.write(datetime.strftime(curr_time, time_fmt))

        return data

    async def load_songs(self) -> list[Song]:
        filepath = self.data_path + '/songs'
        url = 'http://api.smx.573.no/songs'
        data = await self.load_data_incremental(filepath, url)
        data = [Song(**song) for song in data]
        return data

    async def load_charts(self) -> list[Chart]:
        filepath = self.data_path + '/charts'
        url = 'http://api.smx.573.no/charts'
        data = await self.load_data_incremental(filepath, url)
        data = [Chart(**chart) for chart in data]
        return data

    async def load_scores(self, params):
        url = 'http://api.smx.573.no/scores'
        data = await self.load_from_url(url, params)
        scores = []
        for raw_score in data:
            raw_score["chart"] = Chart(**raw_score["chart"])
            raw_score["song"] = Song(**raw_score["song"])
            raw_score["gamer"] = Gamer(**raw_score["gamer"])
            scores.append(Score(**raw_score))
        return scores

    # specific support for certain fields
    async def load_entrant_scores(
            self,
            *,
            entrant_name: str,
            start: datetime | None = None,
            end: datetime | None = None,
            score_gte: int | None = None,
            score_lte: int | None = None,
            difficulty: list[int] | None = None,
            difficulty_name: str | None = None,
            chart_ids: list[int] | None = None,
            sort_field: str | None = None,
            order: str | None = None,
            get_max_only: bool = False,
            take: int | None = None,
        ):
        # Required params
        params = {}
        params['gamer.username'] = entrant_name

        # Optional params
        if start is not None or end is not None:
            params['created_at'] = {}
            if start:
                params['created_at']['gte'] = str(start)
            if end:
                params['created_at']['lte'] = str(end)
        if score_gte is not None or score_lte is not None:
            params['score'] = {}
            if score_gte:
                params['score']['gte'] = score_gte
            if score_lte:
                params['score']['lte'] = score_lte
        self.update_dict_if_not_null(params, 'chart.difficulty', difficulty)
        self.update_dict_if_not_null(params, 'chart.difficulty_name', difficulty_name)
        self.update_dict_if_not_null(params, 'chart.id', chart_ids)
        self.update_dict_if_not_null(params, '_sort', sort_field)
        self.update_dict_if_not_null(params, '_order', order)
        if get_max_only:
            params['_group_by'] = 'song_chart_id'
        self.update_dict_if_not_null(params, '_take', take)
        data = await self.load_scores(params)
        print(f"Returned {len(data)} scores for {entrant_name=}")
        return data

    def exec_load_entrant_scores(self, coroutines) -> list[list[Score]]:
        return self._event_loop.run_until_complete(self.run_tasks_in_aiohttp_client(coroutines))

    def update_dict_if_not_null(self, dict, key, value):
        if value is not None:
            dict[key] = value

    def filter_charts_by_song(self, song_info):
        for song in song_info:
            for s in self.songs:
                if song['title'].casefold() == s.title.casefold():
                    song['id'] = s._id
                    break
        chart_ids = []
        for song in song_info:
            for chart in self.charts:
                if (
                    song['id'] == chart.song_id
                    and song['difficulty'] == chart.difficulty
                    and (
                        song.get('difficulty_name') is None
                        or chart.difficulty_name.startswith(song['difficulty_name'])
                    )
                ):
                    chart_ids.append(chart._id)
                    song['chart_id'] = chart._id
                    break
        return chart_ids


"""
Useful fields

songs.title, songs.subtitle - plaintext names of song

songs.id == charts.song_id

charts.id - used for looking up scores for specific charts
charts.is_enabled - check this for valid officials
charts.difficulty - block rating
"""
if __name__ == '__main__':
    debug = True
    
    sf = ScoreFetcher()

    # load event configuration
    #   pull from file eventually
    start = datetime(year=2024, month=11, day=1)
    end = datetime(year=2024, month=11, day=13)
    entrants = [
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
    chart_ids = sf.filter_charts_by_song(song_info)

    
    # load score data asynchronously
    searches = []
    for entrant in entrants:
        for chart_id in chart_ids:
            searches.append(
                sf.load_entrant_scores(
                    entrant_name=entrant,
                    start=start,
                    end=end,
                    chart_ids=chart_id,
                    sort_field=sort,
                    order=order,
                    take=num_tries_to_count
                )
            )
    all_results = sf.exec_load_entrant_scores(searches)
    with open('test_bulk.json', 'w') as of:
        json.dump(all_results, of)
    for result in all_results:
        for score in result:
            print(' '.join([score.gamer.username, score.song.title, str(score.score)]))