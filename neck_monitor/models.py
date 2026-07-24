from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NeckSensorSample:
    score: int
    state: str
    pitch: float
    roll: float
    mode: str
    timestamp: datetime
    yaw: float
    pressure: float
