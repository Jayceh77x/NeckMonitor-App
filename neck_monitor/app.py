import sys

from PySide6.QtWidgets import QApplication

from neck_monitor.bluetooth.manager import BluetoothManager
from neck_monitor.data.cache import SensorDataCache
from neck_monitor.data.parser import JsonLineStreamDecoder, SensorDataParser
from neck_monitor.ui.main_window import MainWindow


class NeckMonitorApp:
    def __init__(self) -> None:
        self.parser = SensorDataParser()
        self.stream_decoder = JsonLineStreamDecoder()
        self.cache = SensorDataCache(max_size=300)
        self.bluetooth = BluetoothManager(
            port_name="COM8",
            baud_rate=115200,
            source_mode=BluetoothManager.SOURCE_MOCK,
        )
        self.window = MainWindow()

        self.bluetooth.raw_data_received.connect(self._handle_raw_data)
        self.bluetooth.connection_changed.connect(self.window.update_bluetooth_status)
        self.bluetooth.connection_changed.connect(self._handle_connection_changed)
        self.bluetooth.error_occurred.connect(self.window.show_connection_error)
        self.bluetooth.source_changed.connect(self.window.update_data_source)
        self.window.start_requested.connect(self.bluetooth.start)
        self.window.stop_requested.connect(self.bluetooth.stop)
        self.window.source_switch_requested.connect(self._handle_source_switch)
        self.window.update_data_source(self.bluetooth.source_mode)

    def start(self) -> None:
        self.window.show()
        self.bluetooth.start()

    def _handle_raw_data(self, chunk: bytes | str) -> None:
        try:
            payloads = self.stream_decoder.feed(chunk)
        except ValueError as exc:
            self.window.show_data_error(str(exc))
            return

        for payload in payloads:
            try:
                sample = self.parser.parse(payload)
            except (TypeError, ValueError) as exc:
                self.window.show_data_error(str(exc))
                continue
            self.cache.append(sample)
            self.window.update_sample(sample, sample_count=len(self.cache))

    def _handle_connection_changed(self, connected: bool) -> None:
        if connected:
            self.stream_decoder.reset()

    def _handle_source_switch(self, source_mode: str) -> None:
        self.stream_decoder.reset()
        self.bluetooth.switch_source(source_mode)


def run() -> int:
    qt_app = QApplication(sys.argv)
    app = NeckMonitorApp()
    app.start()
    return qt_app.exec()
