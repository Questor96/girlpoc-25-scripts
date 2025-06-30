from dataclasses import dataclass

@dataclass
class Gamer:
    _id: int
    country: str
    description: str
    hex_color: str
    id: int
    picture_path: str
    private: bool
    published_edits: int
    rival: int
    username: str