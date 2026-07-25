import json
import math
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal


class BluetoothManager(QObject):
    raw_data_received = Signal(object)
    connection_changed = Signal(bool)

    def __init__(self, interval_ms: int = 800) -> None:
        super().__init__()
        self._tick = 0
        self._connected = False
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._emit_jdy24m_sample)

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        self._set_connected(True)
        if not self._timer.isActive():
            self._timer.start()
        self._emit_jdy24m_sample()

    def stop(self) -> None:
        self._timer.stop()
        self._set_connected(False)

    def _set_connected(self, connected: bool) -> None:
        if self._connected == connected:
            return
        self._connected = connected
        self.connection_changed.emit(connected)

    def _emit_jdy24m_sample(self) -> None:
        self._tick += 1
        phase = self._tick / 7
        pitch = math.sin(phase) * 24
        roll = math.cos(phase * 0.75) * 16

        state = self._classify_state(pitch, roll)
        score = self._calculate_score(pitch, roll)
        alert = state != "正常" and self._tick % 8 == 0
        payload = {
            "version": 1,
            "seq": self._tick,
            "score": score,
            "state": state,
            "pitch": round(pitch, 2),
            "roll": round(roll, 2),
            "mode": "JDY-24M_SIM",
            "confidence": round(0.91 + 0.06 * abs(math.cos(phase)), 3),
            "alert": int(alert),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        self.raw_data_received.emit(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def _classify_state(pitch: float, roll: float) -> str:
        if pitch < -18:
            return "低头异常"
        if pitch > 18:
            return "仰头异常"
        if abs(roll) > 12:
            return "侧倾异常"
        return "正常"

    @staticmethod
    def _calculate_score(pitch: float, roll: float) -> int:
        penalty = abs(pitch) * 1.2 + abs(roll) * 1.5
        return max(0, min(100, round(100 - penalty)))
