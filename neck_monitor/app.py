import sys

from PySide6.QtWidgets import QApplication

from neck_monitor.bluetooth.mock_source import MockDataSource
from neck_monitor.data.cache import SensorDataCache
from neck_monitor.data.parser import SensorDataParser
from neck_monitor.ui.main_window import MainWindow


class NeckMonitorApp:
    def __init__(self) -> None:
        self.parser = SensorDataParser()
        self.cache = SensorDataCache(max_size=300)
        self.source = MockDataSource(interval_ms=1000)
        self.window = MainWindow()

        self.source.raw_data_received.connect(self._handle_raw_data)
        self.window.start_requested.connect(self.source.start)
        self.window.stop_requested.connect(self.source.stop)

    def start(self) -> None:
        self.window.show()
        self.source.start()

    def _handle_raw_data(self, payload: str) -> None:
        sample = self.parser.parse(payload)
        self.cache.append(sample)
        self.window.update_sample(sample, sample_count=len(self.cache))


def run() -> int:
    qt_app = QApplication(sys.argv)
    app = NeckMonitorApp()
    app.start()
    return qt_app.exec()

