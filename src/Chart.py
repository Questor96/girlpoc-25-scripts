from dataclasses import dataclass

@dataclass
class Chart:
    _id: int
    created_at: str  # datetime
    difficulty: int
    difficulty_display: str
    difficulty_id: int
    difficulty_name: str
    game_difficulty_id: int
    graph: list[float]
    id: int
    is_enabled: bool
    meter: int
    pass_count: int
    play_count: int
    song_id: int
    steps_author: str
    steps_index: int
    updated_at: str  # datetime
