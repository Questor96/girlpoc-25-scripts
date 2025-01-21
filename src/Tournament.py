from src.Chart import Chart
from src.Score import Score
from src.Player import Player
from src.ScoreFetcher import ScoreFetcher

from gspread.worksheet import Worksheet
from gspread.cell import Cell

sf = ScoreFetcher()
sf.debug = False

class GauntletTournament:
    max_difficulty = 26

    def __init__(
        self,
        name: str,
        start_date: str,
        end_date: str,
        attempts_to_count: int,
        ineligible_difficulty: int = None,
        ineligible_score: int = None
    ):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.attempts_to_count = attempts_to_count
        self.ineligible_difficulty = ineligible_difficulty
        self.ineligible_score = ineligible_score
        
        self.players: list[Player] = []
        self.charts: list[Chart] = []
    
    @property
    def chart_ids(self):
        return [chart.id for chart in self.charts]

    def load_players(self, player_names) -> None:
        if not self.ineligible_score or not self.ineligible_difficulty:
            self.players = [
                Player(name, True)
                for name in player_names
            ]
        else:
            searches = []
            for name in player_names:
                searches.append(sf.load_player_scores(
                    player_name=name,
                    difficulty=list(range(self.ineligible_difficulty, self.max_difficulty)),
                    score_gte=self.ineligible_score,
                    end=self.start_date,  # only disqualify based on scores beforehand
                    take=1  # only need one score
                ))
            results = sf.exec_load_player_scores(searches)
            for index in range(len(player_names)):
                self.players.append(Player(player_names[index], not len(results[index]) > 0))

    def load_charts(self, gauntlet_json) -> None:
        sf.filter_charts_by_song(gauntlet_json)
        self.charts = [
            Chart(
                id = song["chart_id"],
                song_title = song["title"],
                difficulty = song["difficulty"]
            )
            for song in gauntlet_json
        ]

    def get_all_scores(self) -> None:
        searches = []
        for player in self.players:
            searches.append(
                sf.load_player_scores(
                player_name=player.name,
                chart_ids=self.chart_ids,
                start=self.start_date,
                end=self.end_date,
                sort_field="created_at",
                order="asc"
            ))
        results = sf.exec_load_player_scores(searches)
        for index in range(len(self.players)):
            player = self.players[index]
            result = results[index]
                
            score_counter = {
                chart_id: 0
                for chart_id in self.chart_ids
            }
            for raw_score in result:
                chart_id = raw_score["song_chart_id"]
                if score_counter[chart_id] <= self.attempts_to_count:
                    [chart] = [chart for chart in self.charts if chart.id == chart_id]
                    player.scores.append(Score(chart, raw_score["score"]))
                    score_counter[chart_id] += 1
                else:
                    continue
            player.finalize_scores()
    
    """
    Results Table Template
        1           2       3       4       ...
    1   <empty>     song1   song2   song3   ...
    2   player_name score1  score2  score3
    3   player_name score1  score2  score3
    N
    """

    def report_results(self, worksheet: Worksheet) -> None:
        row = 1
        self._write_results_header_to_worksheet(worksheet, row)
        for player in self.players:
            if player.has_scores:
                row += 1
                self._write_results_row_to_worksheet(worksheet, row, player)

    def _write_results_header_to_worksheet(self, worksheet: Worksheet, row: int) -> None:
        cells = []
        col = 2
        cells.append(Cell(row, col, "Eligible for Ranking"))
        col += 1
        for chart in self.charts:
            cells.append(Cell(row, col, chart.song_title))
            col += 1
        worksheet.update_cells(cells)

    def _write_results_row_to_worksheet(self, worksheet: Worksheet, row, player: Player) -> None:
        cells = []
        col = 1 
        cells.append(Cell(row, col, player.name))
        col += 1
        cells.append(Cell(row, col, player.can_compete))
        for chart in self.charts:
            col += 1
            any_score = [score for score in player.scores if score.chart == chart]
            if not any_score:
                cells.append(Cell(row, col, 0))
            else:
                cells.append(Cell(row, col, any_score[0].value))
        worksheet.update_cells(cells)