from src.Score import Score

class Entrant:
    def __init__(self, name: str, eligible_for_ranking: bool):
        self.name = name
        self.eligible_for_ranking = eligible_for_ranking
        self._scores: list[Score] = []

    @property
    def scores(self) -> list[Score]:
        return self._scores

    def set_scores(self, scores: list[Score]):
        self._scores = scores

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

    def maximize_scores(self):
        unique_chart_ids = {score.chart._id for score in self.scores}
        maximized_scores = []
        for chart_id in unique_chart_ids:
            max_score_for_chart = self._maximize_score_for_chart(chart_id)
            if max_score_for_chart:
                maximized_scores.append(max_score_for_chart)
        self._scores = maximized_scores

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