import asyncio
import threading

from PySide6.QtCore import QObject, QThread, Signal


FFE1_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"


class _BleWorker(QThread):
    raw_data_received = Signal(object)
    connection_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(
        self,
        device_name: str,
        address: str | None,
        char_uuid: str,
        scan_timeout: float,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._device_name = device_name
        self._address = address
        self._char_uuid = char_uuid
        self._scan_timeout = scan_timeout
        self._stop_requested = threading.Event()

    def stop(self) -> None:
        self._stop_requested.set()

    def run(self) -> None:
        try:
            asyncio.run(self._run_async())
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            self.connection_changed.emit(False)

    async def _run_async(self) -> None:
        try:
            from bleak import BleakClient, BleakScanner
        except ImportError as exc:
            raise RuntimeError("未安装 bleak，请先运行 python -m pip install bleak") from exc

        target = await self._resolve_target(BleakScanner)

        async with BleakClient(target) as client:
            if not client.is_connected:
                raise RuntimeError("BLE 连接失败")

            self.connection_changed.emit(True)

            def on_notify(_: object, data: bytearray) -> None:
                if data:
                    self.raw_data_received.emit(bytes(data))

            try:
                await client.start_notify(self._char_uuid, on_notify)
            except Exception as exc:
                raise RuntimeError(f"无法订阅 FFE1 特征 {self._char_uuid}: {exc}") from exc

            try:
                while not self._stop_requested.is_set() and client.is_connected:
                    await asyncio.sleep(0.1)
            finally:
                try:
                    await client.stop_notify(self._char_uuid)
                except Exception:
                    pass
                self.connection_changed.emit(False)

    async def _resolve_target(self, scanner_type: type) -> object:
        if self._address:
            return self._address

        devices = await scanner_type.discover(timeout=self._scan_timeout)
        matches = [
            device
            for device in devices
            if self._device_name.lower() in (device.name or "").lower()
        ]

        if not matches:
            names = ", ".join(device.name or "(no name)" for device in devices[:8])
            suffix = f"。附近设备：{names}" if names else ""
            raise RuntimeError(f"未找到名称包含 {self._device_name!r} 的 BLE 设备{suffix}")

        if len(matches) > 1:
            choices = ", ".join(f"{device.name or '(no name)'} {device.address}" for device in matches)
            raise RuntimeError(f"找到多个匹配设备，请设置固定地址：{choices}")

        return matches[0]


class BluetoothBleClient(QObject):
    raw_data_received = Signal(object)
    connection_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(
        self,
        device_name: str = "JDY-24M",
        address: str | None = None,
        char_uuid: str = FFE1_UUID,
        scan_timeout: float = 5.0,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._device_name = device_name
        self._address = address
        self._char_uuid = char_uuid
        self._scan_timeout = scan_timeout
        self._connected = False
        self._worker: _BleWorker | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect_device(self) -> None:
        self.disconnect_device()
        self._worker = _BleWorker(
            device_name=self._device_name,
            address=self._address,
            char_uuid=self._char_uuid,
            scan_timeout=self._scan_timeout,
        )
        self._worker.raw_data_received.connect(self.raw_data_received)
        self._worker.connection_changed.connect(self._set_connected)
        self._worker.error_occurred.connect(self.error_occurred)
        self._worker.finished.connect(self._handle_worker_finished)
        self._worker.start()

    def disconnect_device(self) -> None:
        if self._worker is None:
            self._set_connected(False)
            return

        self._worker.stop()
        if not self._worker.wait(3000):
            self._worker.terminate()
            self._worker.wait(1000)
        self._worker = None
        self._set_connected(False)

    def _set_connected(self, connected: bool) -> None:
        if self._connected == connected:
            return
        self._connected = connected
        self.connection_changed.emit(connected)

    def _handle_worker_finished(self) -> None:
        self._worker = None
        self._set_connected(False)
