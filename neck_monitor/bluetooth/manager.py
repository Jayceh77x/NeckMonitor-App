from PySide6.QtCore import QObject, Signal

from neck_monitor.bluetooth.ble_client import BluetoothBleClient, FEE1_UUID
from neck_monitor.bluetooth.client import BluetoothSerialClient
from neck_monitor.bluetooth.mock_source import MockDataSource


class BluetoothManager(QObject):
    raw_data_received = Signal(object)
    connection_changed = Signal(bool)
    error_occurred = Signal(str)
    source_changed = Signal(str)

    SOURCE_MOCK = "mock"
    SOURCE_SERIAL = "serial"
    SOURCE_BLE = "ble"

    def __init__(
        self,
        port_name: str = "COM8",
        baud_rate: int = 115200,
        ble_name: str = "JDY-24M",
        ble_address: str | None = None,
        ble_char_uuid: str = FEE1_UUID,
        interval_ms: int = 800,
        simulation: bool = False,
        source_mode: str | None = None,
    ) -> None:
        super().__init__()
        self._port_name = port_name
        self._baud_rate = baud_rate
        self._ble_name = ble_name
        self._ble_address = ble_address
        self._source_mode = self._normalize_source_mode(
            source_mode or (self.SOURCE_MOCK if simulation else self.SOURCE_SERIAL)
        )
        self._connected = False

        self._mock_source = MockDataSource(interval_ms=interval_ms, parent=self)
        self._mock_source.raw_data_received.connect(self._forward_raw_data)

        self._serial_client = BluetoothSerialClient(self)
        self._serial_client.raw_data_received.connect(self._forward_raw_data)
        self._serial_client.connection_changed.connect(self._set_connected)
        self._serial_client.error_occurred.connect(self._handle_serial_error)

        self._ble_client = BluetoothBleClient(
            device_name=ble_name,
            address=ble_address,
            char_uuid=ble_char_uuid,
            parent=self,
        )
        self._ble_client.raw_data_received.connect(self._forward_raw_data)
        self._ble_client.connection_changed.connect(self._set_connected)
        self._ble_client.error_occurred.connect(self._handle_ble_error)

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def source_mode(self) -> str:
        return self._source_mode

    def start(self) -> None:
        if self._source_mode == self.SOURCE_BLE:
            self._ble_client.connect_device()
            return

        if self._source_mode == self.SOURCE_SERIAL:
            self._serial_client.connect_device(self._port_name, self._baud_rate)
            return

        self._set_connected(True)
        self._mock_source.start()

    def stop(self) -> None:
        self._mock_source.stop()
        self._serial_client.disconnect_device()
        self._ble_client.disconnect_device()
        self._set_connected(False)

    def switch_source(self, source_mode: str) -> None:
        next_source = self._normalize_source_mode(source_mode)
        if next_source == self._source_mode:
            if not self._connected:
                self.start()
            return

        self.stop()
        self._source_mode = next_source
        self.source_changed.emit(next_source)
        self.start()

    def _set_connected(self, connected: bool) -> None:
        if self._connected == connected:
            return
        self._connected = connected
        self.connection_changed.emit(connected)

    def _handle_serial_error(self, message: str) -> None:
        self.error_occurred.emit(f"{self._port_name}: {message}")

    def _handle_ble_error(self, message: str) -> None:
        target = self._ble_address or self._ble_name
        self.error_occurred.emit(f"{target}: {message}")

    def _forward_raw_data(self, chunk: object) -> None:
        self.raw_data_received.emit(chunk)

    @staticmethod
    def _normalize_source_mode(source_mode: str) -> str:
        normalized = source_mode.strip().lower()
        if normalized in {"mock", "simulation", "sim"}:
            return BluetoothManager.SOURCE_MOCK
        if normalized in {"ble", "jdy", "ffe1", "real", "bluetooth"}:
            return BluetoothManager.SOURCE_BLE
        if normalized in {"serial", "com", "uart"}:
            return BluetoothManager.SOURCE_SERIAL
        raise ValueError(f"Unsupported data source: {source_mode}")
