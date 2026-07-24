from datetime import datetime

from neck_monitor.models import NeckSensorSample


class SensorDataParser:
    def parse(self, payload: str) -> NeckSensorSample:
        parts = [part.strip() for part in payload.split(",")]
        if len(parts) != 5:
            raise ValueError(f"无效数据帧：{payload!r}")

        pitch, roll, yaw, pressure, timestamp = parts
        return NeckSensorSample(
            pitch=float(pitch),
            roll=float(roll),
            yaw=float(yaw),
            pressure=float(pressure),
            timestamp=datetime.fromisoformat(timestamp),
        )

