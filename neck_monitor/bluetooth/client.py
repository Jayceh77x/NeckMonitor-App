from PySide6.QtCore import QObject, Signal
from PySide6.QtSerialPort import QSerialPort


class BluetoothSerialClient(QObject):
    raw_data_received = Signal(object)
    connection_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._connected = False
        self._serial = QSerialPort(self)
        self._serial.readyRead.connect(self._read_available)
        self._serial.errorOccurred.connect(self._handle_serial_error)

    @property
    def is_connected(self) -> bool:
        return self._connected and self._serial.isOpen()

    def connect_device(self, port_name: str, baud_rate: int = 115200) -> None:
        if self._serial.isOpen():
            self._serial.close()

        self._serial.setPortName(port_name)
        self._serial.setBaudRate(baud_rate)
        self._serial.setDataBits(QSerialPort.DataBits.Data8)
        self._serial.setParity(QSerialPort.Parity.NoParity)
        self._serial.setStopBits(QSerialPort.StopBits.OneStop)
        self._serial.setFlowControl(QSerialPort.FlowControl.NoFlowControl)

        if not self._serial.open(QSerialPort.OpenModeFlag.ReadOnly):
            self._set_connected(False)
            self.error_occurred.emit(
                f"无法打开蓝牙串口 {port_name}（{baud_rate} 8N1）："
                f"{self._serial.errorString()}"
            )
            return

        self._set_connected(True)

    def disconnect_device(self) -> None:
        if self._serial.isOpen():
            self._serial.close()
        self._set_connected(False)

    def _set_connected(self, connected: bool) -> None:
        if self._connected == connected:
            return
        self._connected = connected
        self.connection_changed.emit(connected)

    def _read_available(self) -> None:
        chunk = bytes(self._serial.readAll())
        if chunk:
            self.raw_data_received.emit(chunk)

    def _handle_serial_error(self, error: QSerialPort.SerialPortError) -> None:
        if error == QSerialPort.SerialPortError.NoError:
            return

        message = self._serial.errorString()
        if error == QSerialPort.SerialPortError.ResourceError:
            self.disconnect_device()
        if message:
            self.error_occurred.emit(message)
