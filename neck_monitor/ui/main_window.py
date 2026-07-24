from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
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
        self.resize(980, 620)
        self._abnormal_count = 0

        self.health_score_value = QLabel("100")
        self.posture_value = QLabel("等待数据")
        self.abnormal_count_value = QLabel("0")
        self.bluetooth_status_value = QLabel("模拟数据")

        self.pitch_value = QLabel("--")
        self.roll_value = QLabel("--")
        self.ai_status_value = QLabel("未启用")
        self.confidence_value = QLabel("--")
        self.history_table = QTableWidget(0, 6)

        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f5f7fb;
            }
            QLabel {
                color: #1f2937;
                font-size: 14px;
            }
            QTabWidget::pane {
                border: 1px solid #d9e0ea;
                border-radius: 8px;
                background: #ffffff;
            }
            QTabBar::tab {
                padding: 10px 18px;
                margin-right: 4px;
                border: 1px solid #d9e0ea;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: #eef2f7;
                color: #42526b;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0f172a;
                font-weight: 600;
            }
            QPushButton {
                min-height: 34px;
                padding: 0 18px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
                color: #0f172a;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #edf6ff;
                border-color: #60a5fa;
            }
            QTableWidget {
                border: none;
                gridline-color: #e5e7eb;
                selection-background-color: #dbeafe;
            }
            QHeaderView::section {
                background: #f1f5f9;
                color: #334155;
                border: none;
                border-bottom: 1px solid #d9e0ea;
                padding: 8px;
                font-weight: 600;
            }
            """
        )

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        header = self._build_header()
        tabs = QTabWidget()
        tabs.addTab(self._build_dashboard_page(), "首页仪表盘")
        tabs.addTab(self._build_realtime_page(), "实时数据")
        tabs.addTab(self._build_history_page(), "历史记录")

        root.addWidget(header)
        root.addWidget(tabs, 1)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("当前使用模拟数据源，蓝牙串口接口已预留")

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title_area = QVBoxLayout()
        title = QLabel("智能颈椎监测")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #0f172a;")
        subtitle = QLabel("STM32 数据展示端")
        subtitle.setStyleSheet("color: #64748b;")
        title_area.addWidget(title)
        title_area.addWidget(subtitle)

        start_button = QPushButton("开始接收")
        stop_button = QPushButton("停止接收")
        start_button.clicked.connect(self._start_clicked)
        stop_button.clicked.connect(self._stop_clicked)

        layout.addLayout(title_area)
        layout.addStretch(1)
        layout.addWidget(start_button)
        layout.addWidget(stop_button)
        return header

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)

        layout.addWidget(
            self._metric_card("健康评分", self.health_score_value, "分", "#0f766e"),
            0,
            0,
        )
        layout.addWidget(
            self._metric_card("当前姿态", self.posture_value, "", "#2563eb"),
            0,
            1,
        )
        layout.addWidget(
            self._metric_card("异常次数", self.abnormal_count_value, "次", "#dc2626"),
            1,
            0,
        )
        layout.addWidget(
            self._metric_card("蓝牙状态", self.bluetooth_status_value, "", "#475569"),
            1,
            1,
        )

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        return page

    def _build_realtime_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)

        layout.addWidget(self._metric_card("Pitch", self.pitch_value, "deg", "#2563eb"), 0, 0)
        layout.addWidget(self._metric_card("Roll", self.roll_value, "deg", "#7c3aed"), 0, 1)
        layout.addWidget(self._metric_card("AI状态", self.ai_status_value, "", "#64748b"), 1, 0)
        layout.addWidget(self._metric_card("置信度", self.confidence_value, "", "#64748b"), 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)

        self.history_table.setHorizontalHeaderLabels(
            ["时间", "Pitch", "Roll", "Yaw", "压力", "姿态"]
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)

        layout.addWidget(self.history_table)
        return page

    def _metric_card(
        self, title: str, value_widget: QLabel, unit: str, accent_color: str
    ) -> QWidget:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card.setStyleSheet(
            f"""
            QFrame {{
                background: #ffffff;
                border: 1px solid #d9e0ea;
                border-radius: 8px;
            }}
            QLabel#accent {{
                background: {accent_color};
                border-radius: 3px;
                min-width: 34px;
                max-width: 34px;
                min-height: 4px;
                max-height: 4px;
            }}
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        accent = QLabel()
        accent.setObjectName("accent")

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #64748b; font-weight: 600;")

        value_row = QHBoxLayout()
        value_widget.setStyleSheet("font-size: 34px; font-weight: 700; color: #0f172a;")
        value_widget.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #64748b; font-weight: 600;")
        value_row.addWidget(value_widget)
        value_row.addWidget(unit_label)
        value_row.addStretch(1)

        layout.addWidget(accent)
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addLayout(value_row)
        return card

    def update_sample(self, sample: NeckSensorSample, sample_count: int) -> None:
        posture = self._classify_posture(sample)
        abnormal = posture != "正常"
        if abnormal:
            self._abnormal_count += 1

        health_score = max(0, 100 - self._abnormal_count * 2)

        self.health_score_value.setText(str(health_score))
        self.posture_value.setText(posture)
        self.abnormal_count_value.setText(str(self._abnormal_count))
        self.bluetooth_status_value.setText("模拟接收中")

        self.pitch_value.setText(f"{sample.pitch:.1f}")
        self.roll_value.setText(f"{sample.roll:.1f}")
        self.ai_status_value.setText("未启用")
        self.confidence_value.setText("--")

        self._append_history(sample, posture)
        self.statusBar().showMessage(f"已接收 {sample_count} 条模拟数据")

    def _append_history(self, sample: NeckSensorSample, posture: str) -> None:
        self.history_table.insertRow(0)
        values = [
            sample.timestamp.strftime("%H:%M:%S"),
            f"{sample.pitch:.1f}",
            f"{sample.roll:.1f}",
            f"{sample.yaw:.1f}",
            f"{sample.pressure:.2f}",
            posture,
        ]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(0, column, item)

        while self.history_table.rowCount() > 100:
            self.history_table.removeRow(self.history_table.rowCount() - 1)

    def _start_clicked(self) -> None:
        self.bluetooth_status_value.setText("模拟接收中")
        self.start_requested.emit()

    def _stop_clicked(self) -> None:
        self.bluetooth_status_value.setText("已停止")
        self.stop_requested.emit()
        self.statusBar().showMessage("模拟数据接收已停止")

    @staticmethod
    def _classify_posture(sample: NeckSensorSample) -> str:
        if abs(sample.pitch) > 20:
            return "低头异常" if sample.pitch < 0 else "仰头异常"
        if abs(sample.roll) > 15:
            return "侧倾异常"
        return "正常"
