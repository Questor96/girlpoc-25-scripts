from dataclasses import dataclass

from src.Chart import Chart
from src.Song import Song
from src.Gamer import Gamer

@dataclass
class Score:
    _id: int
    calories: int
    chart: Chart
    cleared: bool
    created_at: str  # datetime
    early: int
    flags: int
    full_combo: bool
    gamer: Gamer
    gamer_id: int
    global_flags: int
    grade: int
    green: int
    id: int
    late: int
    max_combo: int
    misses: int
    music_speed: int
    perfect1: int
    perfect2: int
    personal_best: int
    personal_best_previous: int
    red: int
    score: int
    side: str
    song: Song
    song_chart_id: int
    steps: int
    updated_at: str  # datetime
    uuid: str
    yellow: int

    def ladder_points(
        self,
        score_floor: int = 0,
        difficulty_scaling: float = 2.0,
        divisor: float = 1000.0
    ) -> float:
        return max(
            (self.score - score_floor) * (self.chart.difficulty ** difficulty_scaling) / divisor,
            0
        )