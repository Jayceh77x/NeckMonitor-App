import json
import math
from datetime import datetime

from neck_monitor.models import NeckSensorSample


class JsonLineStreamDecoder:
    """Split a serial byte stream into UTF-8 JSON frames terminated by newlines."""

    def __init__(self, max_buffer_size: int = 16_384) -> None:
        self._buffer = bytearray()
        self._max_buffer_size = max_buffer_size

    def feed(self, chunk: bytes | bytearray | memoryview | str) -> list[str]:
        encoded = chunk.encode("utf-8") if isinstance(chunk, str) else bytes(chunk)
        self._buffer.extend(encoded)

        frames: list[str] = []
        while True:
            newline_index = self._buffer.find(b"\n")
            if newline_index < 0:
                break

            frame_bytes = bytes(self._buffer[:newline_index]).rstrip(b"\r")
            del self._buffer[: newline_index + 1]
            if not frame_bytes:
                continue

            try:
                frames.append(frame_bytes.decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise ValueError("蓝牙数据不是有效的 UTF-8 编码") from exc

        if len(self._buffer) > self._max_buffer_size:
            self._buffer.clear()
            raise ValueError("蓝牙接收缓冲区超过限制，未找到完整换行帧")

        return frames

    def reset(self) -> None:
        self._buffer.clear()


class SensorDataParser:
    _STATE_NAMES = {
        "NORMAL": "正常",
        "HEAD_DOWN": "低头异常",
        "HEAD_UP": "仰头异常",
        "TILT_LEFT": "左倾异常",
        "TILT_RIGHT": "右倾异常",
        "TILT": "侧倾异常",
    }

    def parse(self, payload: str) -> NeckSensorSample:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("JDY-24M JSON 顶层必须是对象")
        version = int(data.get("version", 1))
        if version != 1:
            raise ValueError(f"不支持的蓝牙协议版本：{version}")
        required_fields = {"score", "state", "pitch", "roll", "mode", "vibration_strength"}
        missing_fields = required_fields.difference(data)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"JDY-24M JSON 数据缺少字段：{missing}")

        timestamp_text = data.get("timestamp")
        timestamp = (
            datetime.fromisoformat(timestamp_text)
            if timestamp_text
            else datetime.now()
        )
        score = int(data["score"])
        pitch = float(data["pitch"])
        roll = float(data["roll"])
        vibration_strength = int(data["vibration_strength"])
        if vibration_strength not in (0, 1, 2):
            raise ValueError("vibration_strength 瀛楁蹇呴』鍦?0-2 鑼冨洿鍐?")
        confidence_value = data.get("confidence")
        confidence = None if confidence_value is None else float(confidence_value)
        if not 0 <= score <= 100:
            raise ValueError("score 字段必须在 0-100 范围内")
        if not math.isfinite(pitch) or not math.isfinite(roll):
            raise ValueError("pitch 和 roll 必须是有限数值")
        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence 字段必须在 0.0-1.0 范围内")
        alert_value = data.get("alert", 0)
        if isinstance(alert_value, bool):
            alert = alert_value
        elif alert_value in (0, 1, "0", "1"):
            alert = bool(int(alert_value))
        elif isinstance(alert_value, str) and alert_value.lower() in ("false", "true"):
            alert = alert_value.lower() == "true"
        else:
            raise ValueError("alert 字段必须为 0、1、false 或 true")
        raw_state = str(data["state"])
        state = self._STATE_NAMES.get(raw_state.upper(), raw_state)
        return NeckSensorSample(
            score=score,
            state=state,
            pitch=pitch,
            roll=roll,
            mode=str(data["mode"]),
            vibration_strength=vibration_strength,
            timestamp=timestamp,
            yaw=float(data.get("yaw", 0.0)),
            pressure=float(data.get("pressure", 0.0)),
            confidence=confidence,
            alert=alert,
        )
