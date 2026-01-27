from dataclasses import dataclass

@dataclass
class EligibilityConfig:
    difficulty: int
    score: int
    count: int = 1

@dataclass
class Eligibility:
    eligible: bool
    difficulty: int | None = None
    score: str | None = None
    count: int | None = None
