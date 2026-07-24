from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from neck_monitor.models import NeckSensorSample


class MainWindow(QMainWindow):
    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NeckMonitor App")
        self.resize(720, 420)

        self.pitch_value = QLabel("--")
        self.roll_value = QLabel("--")
        self.yaw_value = QLabel("--")
        self.pressure_value = QLabel("--")
        self.timestamp_value = QLabel("--")
        self.count_value = QLabel("0")

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("智能颈椎监测数据展示端")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")

        data_group = QGroupBox("实时数据")
        data_layout = QGridLayout(data_group)
        data_layout.setHorizontalSpacing(24)
        data_layout.setVerticalSpacing(14)

        rows = [
            ("前后倾角 Pitch", self.pitch_value, "deg"),
            ("左右倾角 Roll", self.roll_value, "deg"),
            ("旋转角 Yaw", self.yaw_value, "deg"),
            ("压力 Pressure", self.pressure_value, "N"),
            ("采样时间", self.timestamp_value, ""),
            ("缓存数量", self.count_value, "条"),
        ]

        for row_index, (label, value_widget, unit) in enumerate(rows):
            name = QLabel(label)
            unit_label = QLabel(unit)
            value_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_widget.setMinimumWidth(120)
            value_widget.setStyleSheet("font-size: 18px; font-weight: 600;")
            data_layout.addWidget(name, row_index, 0)
            data_layout.addWidget(value_widget, row_index, 1)
            data_layout.addWidget(unit_label, row_index, 2)

        controls = QWidget()
        controls_layout = QGridLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        start_button = QPushButton("开始接收")
        stop_button = QPushButton("停止接收")
        start_button.clicked.connect(self.start_requested.emit)
        stop_button.clicked.connect(self.stop_requested.emit)

        controls_layout.addWidget(start_button, 0, 0)
        controls_layout.addWidget(stop_button, 0, 1)
        controls_layout.setColumnStretch(2, 1)

        root.addWidget(title)
        root.addWidget(data_group)
        root.addWidget(controls)
        root.addStretch(1)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("当前使用模拟数据源")

    def update_sample(self, sample: NeckSensorSample, sample_count: int) -> None:
        self.pitch_value.setText(f"{sample.pitch:.1f}")
        self.roll_value.setText(f"{sample.roll:.1f}")
        self.yaw_value.setText(f"{sample.yaw:.1f}")
        self.pressure_value.setText(f"{sample.pressure:.2f}")
        self.timestamp_value.setText(sample.timestamp.strftime("%H:%M:%S"))
        self.count_value.setText(str(sample_count))

