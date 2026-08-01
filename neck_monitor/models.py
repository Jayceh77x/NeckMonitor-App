from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NeckSensorSample:
    score: int
    state: str
    pitch: float
    roll: float
    mode: str
    vibration_strength: int
    timestamp: datetime
    yaw: float
    pressure: float
    confidence: float | None
    alert: bool
