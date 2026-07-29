import json
import math
import random
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal


class MockDataSource(QObject):
    raw_data_received = Signal(object)

    _SCENARIOS = (
        {"score": 96, "state": "NORMAL", "pitch": 2.0, "roll": 0.8, "confidence": 0.97},
        {"score": 91, "state": "NORMAL", "pitch": 5.5, "roll": -1.5, "confidence": 0.95},
        {"score": 72, "state": "HEAD_DOWN", "pitch": -24.0, "roll": 2.0, "confidence": 0.93},
        {"score": 68, "state": "HEAD_DOWN", "pitch": -29.0, "roll": 4.0, "confidence": 0.94},
        {"score": 87, "state": "NORMAL", "pitch": 7.0, "roll": -2.5, "confidence": 0.96},
        {"score": 76, "state": "HEAD_UP", "pitch": 23.0, "roll": 1.8, "confidence": 0.92},
        {"score": 80, "state": "TILT_LEFT", "pitch": 4.5, "roll": -15.5, "confidence": 0.91},
        {"score": 83, "state": "TILT_RIGHT", "pitch": 3.0, "roll": 14.0, "confidence": 0.92},
    )

    def __init__(self, interval_ms: int = 1000, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tick = 0
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._emit_sample)

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start()
        self._emit_sample()

    def stop(self) -> None:
        self._timer.stop()

    def _emit_sample(self) -> None:
        self._tick += 1
        phase = self._tick / 6
        scenario = self._SCENARIOS[(self._tick // 5) % len(self._SCENARIOS)]
        alert = scenario["state"] != "NORMAL" and self._tick % 12 in (0, 1)

        payload = {
            "version": 1,
            "seq": self._tick,
            "score": scenario["score"],
            "state": scenario["state"],
            "pitch": round(scenario["pitch"] + math.sin(phase) * 1.1, 2),
            "roll": round(scenario["roll"] + math.cos(phase * 0.8) * 0.9, 2),
            "mode": 0,
            "alert": int(alert),
            "confidence": round(scenario["confidence"] + random.uniform(-0.01, 0.01), 3),
            "yaw": round(math.sin(phase * 0.5) * 8, 2),
            "pressure": round(4.5 + random.uniform(-0.25, 0.25), 2),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        self.raw_data_received.emit(json.dumps(payload, ensure_ascii=False) + "\n")
