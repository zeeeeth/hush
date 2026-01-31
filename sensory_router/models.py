from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class StopPoint:
    """Represents a station/stop on the journey."""
    naptan_id: str
    name: str
    arrival_time: datetime
    crowding_score: float = 0.0  # 0.0 to 1.0
    line_id: Optional[str] = None


@dataclass
class RouteLeg:
    """A single leg of a journey (e.g., one tube line segment)."""
    mode: str
    line_name: str
    line_id: str
    duration_minutes: int
    stops: List[StopPoint]
    instruction: str
    departure_point: str
    arrival_point: str


@dataclass
class Route:
    """A complete journey from origin to destination."""
    legs: List[RouteLeg]
    total_duration: int
    departure_time: datetime
    arrival_time: datetime
    sensory_score: float = 0.0
    has_delays: bool = False
    delay_info: str = ""
