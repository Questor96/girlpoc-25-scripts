from src.Score import Score
from src.Eligibility import Eligibility

class Entrant:
    def __init__(self, name: str, eligibilities: list[Eligibility]):
        self.name = name
        self.eligiblities = eligibilities
        self._scores: list[Score] = []

    @property
    def scores(self) -> list[Score]:
        return self._scores

    @property
    def can_compete(self) -> bool:
        return all([eligibility.eligible for eligibility in self.eligiblities])
    
    @property
    def has_scores(self) -> bool:
        nonzero_scores = [
            score for score in self.scores
            if score.score > 0
        ]
        return len(nonzero_scores) > 0

    def set_scores(self, scores: list[Score]):
        self._scores = scores

    def maximize_scores(self):
        unique_chart_ids = {score.chart._id for score in self.scores}
        maximized_scores = []
        for chart_id in unique_chart_ids:
            max_score_for_chart = self._maximize_score_for_chart(chart_id)
            if max_score_for_chart:
                maximized_scores.append(max_score_for_chart)
        self.set_scores(maximized_scores)

    def _maximize_score_for_chart(self, chart_id: int) -> Score | None:
        max_score = None
        filtered_scores = [
            score for score in self._scores
            if score.chart.id == chart_id
        ]
        for score in filtered_scores:
            if not max_score or score.score > max_score.score:
                max_score = score
        return max_score
