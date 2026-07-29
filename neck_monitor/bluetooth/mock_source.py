import math
import random
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal


class MockDataSource(QObject):
    raw_data_received = Signal(str)

    def __init__(self, interval_ms: int = 1000) -> None:
        super().__init__()
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
        phase = self._tick / 8
        pitch = math.sin(phase) * 18
        roll = math.cos(phase * 0.8) * 12
        yaw = math.sin(phase * 0.5) * 25
        pressure = 4.5 + random.uniform(-0.35, 0.35)
        timestamp = datetime.now().isoformat(timespec="seconds")

        payload = f"{pitch:.2f},{roll:.2f},{yaw:.2f},{pressure:.2f},{timestamp}"
        self.raw_data_received.emit(payload)
