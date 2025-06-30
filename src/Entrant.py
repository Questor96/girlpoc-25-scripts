from src.Chart import Chart
from src.Score import Score

class Entrant:
    def __init__(self, name: str, eligible_for_ranking: bool):
        self.name = name
        self.eligible_for_ranking = eligible_for_ranking
        self.scores: list[Score] = []
    
    @property
    def can_compete(self) -> bool:
        return self.eligible_for_ranking
    
    @property
    def has_scores(self) -> bool:
        nonzero_scores = len([
            score for score in self.scores
            if score.score > 0
        ])
        return nonzero_scores > 0

    def finalize_scores(self):
        charts = {score.chart for score in self.scores}
        self.scores = [
            Score(chart, self._maximize_score(self.scores, chart).score)
            for chart in charts
        ]

    @staticmethod
    def _maximize_score(scores: list[Score], chart: Chart) -> Score:
        max_score = None
        filtered_scores = [
            score for score in scores
            if score.chart.id == chart.id
        ]
        for score in filtered_scores:
            if not max_score or score.score > max_score.score:
                max_score = score
        return max_score