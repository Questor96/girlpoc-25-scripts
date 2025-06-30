from dataclasses import dataclass

@dataclass
class Song:
    _id: str
    allow_edits: bool
    artist: str
    bpm: str
    cover: str
    cover_path: str
    cover_thumb: str
    created_at: str  # datetime
    extra: dict
    first_beat: int
    first_ms: int
    game_song_id: int
    genre: str
    id: int
    is_enabled: bool
    label: str
    last_beat: int
    last_ms: int
    release_date: str  # datetime
    subtitle: str
    timing_bpms: str
    timing_offset_ms: int
    timing_stops: str
    title: str
    updated_at: str  # datetime
    website: str

    music_filename: str = None
