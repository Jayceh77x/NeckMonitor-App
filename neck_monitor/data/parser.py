import json
from datetime import datetime

from neck_monitor.models import NeckSensorSample


class SensorDataParser:
    def parse(self, payload: str) -> NeckSensorSample:
        data = json.loads(payload)
        required_fields = {"score", "state", "pitch", "roll", "mode"}
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
        return NeckSensorSample(
            score=int(data["score"]),
            state=str(data["state"]),
            pitch=float(data["pitch"]),
            roll=float(data["roll"]),
            mode=str(data["mode"]),
            timestamp=timestamp,
            yaw=float(data.get("yaw", 0.0)),
            pressure=float(data.get("pressure", 0.0)),
        )
