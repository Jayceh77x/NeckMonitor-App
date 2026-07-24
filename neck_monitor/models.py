from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NeckSensorSample:
    pitch: float
    roll: float
    yaw: float
    pressure: float
    timestamp: datetime

