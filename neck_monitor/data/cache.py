from collections import deque
from typing import Deque, Iterable

from neck_monitor.models import NeckSensorSample


class SensorDataCache:
    def __init__(self, max_size: int = 300) -> None:
        self._items: Deque[NeckSensorSample] = deque(maxlen=max_size)

    def append(self, sample: NeckSensorSample) -> None:
        self._items.append(sample)

    def clear(self) -> None:
        self._items.clear()

    def latest(self) -> NeckSensorSample | None:
        if not self._items:
            return None
        return self._items[-1]

    def as_list(self) -> list[NeckSensorSample]:
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterable[NeckSensorSample]:
        return iter(self._items)

