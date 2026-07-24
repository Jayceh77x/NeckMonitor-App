import sys

from PySide6.QtWidgets import QApplication

from neck_monitor.bluetooth.manager import BluetoothManager
from neck_monitor.data.cache import SensorDataCache
from neck_monitor.data.parser import SensorDataParser
from neck_monitor.ui.main_window import MainWindow


class NeckMonitorApp:
    def __init__(self) -> None:
        self.parser = SensorDataParser()
        self.cache = SensorDataCache(max_size=300)
        self.bluetooth = BluetoothManager(interval_ms=800)
        self.window = MainWindow()

        self.bluetooth.raw_data_received.connect(self._handle_raw_data)
        self.bluetooth.connection_changed.connect(self.window.update_bluetooth_status)
        self.window.start_requested.connect(self.bluetooth.start)
        self.window.stop_requested.connect(self.bluetooth.stop)

    def start(self) -> None:
        self.window.show()
        self.bluetooth.start()

    def _handle_raw_data(self, payload: str) -> None:
        sample = self.parser.parse(payload)
        self.cache.append(sample)
        self.window.update_sample(sample, sample_count=len(self.cache))


def run() -> int:
    qt_app = QApplication(sys.argv)
    app = NeckMonitorApp()
    app.start()
    return qt_app.exec()
