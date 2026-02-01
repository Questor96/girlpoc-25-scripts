import asyncio
import aiohttp
import json
from datetime import datetime, UTC
from pathlib import Path

from src.Chart import Chart
from src.Gamer import Gamer
from src.Score import Score
from src.Song import Song


class ScoreFetcher():
    """
    Connector to SMX.573.no API

    Handles url construction and async call management

    API results preformatted as data classes for simple consumption
    """
    def __init__(self, *, debug: bool=False):
        self.debug = debug

        self.data_path = Path(__file__).parent.parent / "data"
        self.songs: list[Song] = []
        self.charts: list[Chart] = []

        # Event Loop and Session for API calls
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)
        self._session: aiohttp.ClientSession = None  # establish placeholder parameter

        # Initialize song and chart lists
        coroutines = [
            self._load_songs(),
            self._load_charts(),
        ]
        [self.songs, self.charts] = self.execute_coroutines(coroutines)
        if self.debug:
            print(str(len(self.songs)) + " songs loaded")
            print(str(len(self.charts)) + " charts loaded")

    def __del__(self):
        # Required to clean up event loop to avoid error on program end
        self._event_loop.close()

    # public functions
    def execute_coroutines(self, coroutines):
        """
        Runs a set of coroutines and returns the results

        :param coroutines: Async function call that is awaitable
        """
        return self._event_loop.run_until_complete(self._run_tasks_in_aiohttp_client(coroutines))

    async def load_entrant_scores(
        self,
        *,
        entrant_name: str,
        start: datetime | None = None,
        end: datetime | None = None,
        score_gte: int | None = None,
        score_lte: int | None = None,
        difficulty: list[int] | None = None,
        difficulty_names: str | list[str] | None = None,
        chart_ids: list[int] | None = None,
        sort_field: str | None = None,
        order: str | None = None,
        get_cleared_only: bool = False,
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
        if get_cleared_only:
            params['cleared'] = True
        if get_max_only:
            params['_group_by'] = 'song_chart_id'
        self._update_dict_if_not_null(params, 'chart.difficulty', difficulty)
        self._update_dict_if_not_null(params, 'chart.difficulty_name', difficulty_names)
        self._update_dict_if_not_null(params, 'chart.id', chart_ids)
        self._update_dict_if_not_null(params, '_sort', sort_field)
        self._update_dict_if_not_null(params, '_order', order)
        self._update_dict_if_not_null(params, '_take', take)

        data = await self._load_scores(params)
        print(f"Returned {len(data)} scores for {entrant_name=}")
        for score in data:
            print('\t', score.score, '\t', score.chart.difficulty, '\t', score.song.title, )
        return data

    # private helpers
    def _update_dict_if_not_null(self, dict, key, value):
        if value is not None:
            dict[key] = value

    # private helpers - async
    async def _run_tasks_in_aiohttp_client(self, coroutines):
        results = []
        async with aiohttp.ClientSession() as session:
            self._session = session
            for coroutine in coroutines:
                result = await coroutine
                results.append(result)
        self._session = None  # reset after close
        return results

    async def _load_from_url(self, url: str, params: dict | None = None):
        """
        Load all results from SMX.573.no API for given url and params
        
        :param url: Base url for the API call
        :type url: str
        :param params: Dict of parameters w/ values, if any
        :type params: dict | None
        """
        if params is None:
            params = {}
        data = []
        complete = False
        params['_skip'] = 0

        # take at most 100 elements per request, per API spec
        initial_take = params.get('_take', None)
        params['_take'] = initial_take if initial_take is not None and initial_take < 100 else 100
        while not complete:
            # grab next set of data
            data += await self._load_from_url_single(url, params)

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

    async def _load_from_url_single(self, url: str, params: dict | None = None):
        """
        private helper for actually executing the API request via url + parameters

        :param url: Base url for the API call
        :type url: str
        :param params: Dict of parameters w/ values, if any
        :type params: dict | None
        """
        # grab active session from instance variable
        session: aiohttp.ClientSession = self._session
        if params is not None:
            if self.debug:
                print(f"{params=}")
            url = f'{url}?params={json.dumps(params)}'
        if self.debug:
            print(f"{url=}")
        response = await session.request('GET', url=url)
        if response.status != 200:
            # TODO: error handling
            print(url, response.status, response.reason)
            return {}
        data = await response.json()
        return data

    async def _load_data_incremental(self, filepath: Path, base_api_url: str):
        """
        Load data from a file, augment w/ updated info from API, then save back to file

        :param filepath: Description
        :param base_api_url: Description
        """
        time_fmt = "%a, %b %d %Y %H:%M:%S"
        upd_at_filepath = str(filepath) + '_updated_at.txt'
        data_filepath = str(filepath) + '_data.json'

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
        # API uses UTC for lookup
        curr_time = datetime.now(UTC)

        # query API for data updated since previous timestamp
        params = {}
        if previous_search:
            params = {"updated_at": {"gt": str(prev_upd_at)}}
        new_data = await self._load_from_url(base_api_url, params)

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

    async def _load_songs(self) -> list[Song]:
        filepath = self.data_path / 'songs'
        url = 'http://api.smx.573.no/songs'
        data = await self._load_data_incremental(filepath, url)
        data = [Song(**song) for song in data]
        return data

    async def _load_charts(self) -> list[Chart]:
        filepath = self.data_path / 'charts'
        url = 'http://api.smx.573.no/charts'
        data = await self._load_data_incremental(filepath, url)
        data = [Chart(**chart) for chart in data]
        return data

    # could be made public
    async def _load_scores(self, params) -> list[Score]:
        url = 'http://api.smx.573.no/scores'
        data = await self._load_from_url(url, params)
        scores = []
        for raw_score in data:
            raw_score["chart"] = Chart(**raw_score["chart"])
            raw_score["song"] = Song(**raw_score["song"])
            raw_score["gamer"] = Gamer(**raw_score["gamer"])
            scores.append(Score(**raw_score))
        return scores
