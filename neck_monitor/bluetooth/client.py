from PySide6.QtCore import QObject, Signal


class BluetoothSerialClient(QObject):
    raw_data_received = Signal(str)
    connection_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect_device(self, port_name: str, baud_rate: int = 115200) -> None:
        self._set_connected(False)
        self.error_occurred.emit(
            f"蓝牙串口尚未接入：port={port_name}, baud_rate={baud_rate}"
        )

    def disconnect_device(self) -> None:
        self._set_connected(False)

    def _set_connected(self, connected: bool) -> None:
        if self._connected == connected:
            return
        self._connected = connected
        self.connection_changed.emit(connected)

