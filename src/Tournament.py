from src.Chart import Chart
from src.Gamer import Gamer
from src.Entrant import Entrant
from src.Score import Score
from src.Song import Song
from src.ScoreFetcher import ScoreFetcher

from gspread.worksheet import Worksheet
from gspread.cell import Cell

sf = ScoreFetcher()
sf.debug = False

class Tournament:
    def __init__(
        self,
        name: str,
        start_date: str,
        end_date: str
    ):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.charts: list[Chart] = sf.charts
        self.songs: list[Song] = sf.songs
        
        self.entrants: list[Entrant] = []
    
    def load_entrants(self, entrant_names):
        self.entrants = [
            Entrant(name, True)
            for name in entrant_names
        ]

    def get_all_scores(self):
        # implemented by each tournament
        pass

class LadderTournament(Tournament):
    def __init__(
        self,
        name: str,
        start_date: str,
        end_date: str,
        ladder_point_scalar: float,
    ):
        self.ladder_point_scalar = ladder_point_scalar
        super().__init__(
            name=name,
            start_date=start_date,
            end_date=end_date,
        )

    def get_all_scores(self):
        """
        Get best score for every chart
        """
        searches = []
        for entrant in self.entrants:
            searches.append(sf.load_entrant_scores(
                entrant_name=entrant.name,
                start=self.start_date,
                end=self.end_date,
                get_max_only=True,
            ))
        results = sf.exec_load_entrant_scores(searches)
        for index in range(len(self.entrants)):
            entrant = self.entrants[index]
            entrant.scores = results[index]
        self._order_scores_by_ladder_points()

    def _order_scores_by_ladder_points(self):
        for entrant in self.entrants:
            entrant.scores = sorted(
                entrant.scores,
                key=lambda x: x.ladder_points(self.ladder_point_scalar),
                reverse=True
            )


class GauntletTournament(Tournament):
    max_difficulty = 26

    def __init__(
        self,
        name: str,
        start_date: str,
        end_date: str,
        attempts_to_count: int,
        ineligible_difficulty: int = None,
        ineligible_score: int = None,
        ineligible_count: int = None,
    ):
        super().__init__(
            name=name,
            start_date=start_date,
            end_date=end_date
        )
        self.attempts_to_count = attempts_to_count
        self.ineligible_difficulty = ineligible_difficulty
        self.ineligible_score = ineligible_score
        self.ineligible_count = ineligible_count
    
    @property
    def chart_ids(self):
        return [chart.id for chart in self.charts]

    def load_entrants(self, entrant_names):
        if not self.ineligible_score or not self.ineligible_difficulty:
            super().load_entrants(entrant_names=entrant_names)
        else:
            searches = []
            for name in entrant_names:
                searches.append(sf.load_entrant_scores(
                    entrant_name=name,
                    difficulty=list(range(self.ineligible_difficulty, self.max_difficulty)),
                    score_gte=self.ineligible_score,
                    end=self.start_date,  # only disqualify based on scores beforehand
                    take=self.ineligible_count if self.ineligible_count is not None else 1
                ))
            results = sf.exec_load_entrant_scores(searches)
            for index in range(len(entrant_names)):
                self.entrants.append(Entrant(
                    entrant_names[index],
                    not len(results[index]) >= self.ineligible_count
                ))

    def filter_songs_and_charts(self, gauntlet_json) -> None:
        filtered_songs = []
        filtered_charts = []
        for filter in gauntlet_json:
            [song] = [
                song for song in self.songs 
                if song.title.casefold() == str(filter["title"]).casefold()
                or song.subtitle.casefold() == str(filter["title"]).casefold()
            ]
            filtered_songs.append(song)
            
            filtered_charts |= [
                chart for chart in self.charts
                if chart.song_id == song.id
                and chart.difficulty == filter["difficulty"]
                and chart.difficulty_name.casefold().startswith(
                    str(filter["difficulty_name"]).casefold()
                )
            ]
        self.songs = filtered_songs
        self.charts = filtered_charts

    def get_all_scores(self) -> None:
        """
        Best score submitted within the first `attempts_to_count` attempts
            for each chart in the Tournament
        """
        searches = []
        for entrant in self.entrants:
            searches.append(
                sf.load_entrant_scores(
                entrant_name=entrant.name,
                chart_ids=self.chart_ids,
                start=self.start_date,
                end=self.end_date,
                sort_field="created_at",
                order="asc"
            ))
        results = sf.exec_load_entrant_scores(searches)
        for index in range(len(self.entrants)):
            entrant = self.entrants[index]
            result = results[index]
                
            score_counter = {
                chart_id: 0
                for chart_id in self.chart_ids
            }
            for score in result:
                chart_id = score.song_chart_id
                if score_counter[chart_id] <= self.attempts_to_count:
                    entrant.scores.append(score)
                    score_counter[chart_id] += 1
            entrant.finalize_scores()
    
    """
    Results Table Template
        1           2       3       4       ...
    1   <empty>     song1   song2   song3   ...
    2   entrant_name score1  score2  score3
    3   entrant_name score1  score2  score3
    N
    """

    def report_results(self, worksheet: Worksheet) -> None:
        row = 1
        self._write_results_header_to_worksheet(worksheet, row)
        for entrant in self.entrants:
            if entrant.has_scores and entrant.can_compete:
                row += 1
                self._write_results_row_to_worksheet(worksheet, row, entrant)
        for entrant in self.entrants:
            if entrant.has_scores and not entrant.can_compete:
                row += 1
                self._write_results_row_to_worksheet(worksheet, row, entrant)

    def _write_results_header_to_worksheet(self, worksheet: Worksheet, row: int) -> None:
        cells = []
        col = 2
        cells.append(Cell(row, col, "Eligible for Ranking"))
        col += 1
        for chart in self.charts:
            cells.append(Cell(row, col, chart.song_title))
            col += 1
        worksheet.update_cells(cells)

    def _write_results_row_to_worksheet(self, worksheet: Worksheet, row, entrant: Entrant) -> None:
        cells = []
        col = 1 
        cells.append(Cell(row, col, entrant.name))
        col += 1
        cells.append(Cell(row, col, entrant.can_compete))
        for chart in self.charts:
            col += 1
            any_score = [score for score in entrant.scores if score.chart == chart]
            if not any_score:
                cells.append(Cell(row, col, 0))
            else:
                cells.append(Cell(row, col, any_score[0].value))
        worksheet.update_cells(cells)