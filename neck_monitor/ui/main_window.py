from datetime import datetime

from PySide6.QtCore import QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
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
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from neck_monitor.models import NeckSensorSample


class LineChart(QWidget):
    def __init__(self, color: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._label = label
        self._values: list[float] = []
        self.setMinimumHeight(150)

    def set_values(self, values: list[float]) -> None:
        self._values = values[-40:]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(14, 12, -14, -18)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        grid_pen = QPen(QColor("#e5eaf2"))
        grid_pen.setStyle(Qt.DashLine)
        painter.setPen(grid_pen)
        for ratio in (0.25, 0.5, 0.75):
            y = rect.top() + rect.height() * ratio
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))

        painter.setPen(QPen(QColor("#94a3b8")))
        painter.drawText(rect.left(), rect.top() + 12, "30")
        painter.drawText(rect.left(), rect.center().y() + 4, "0")
        painter.drawText(rect.left(), rect.bottom(), "-30")

        if len(self._values) < 2:
            painter.setPen(QPen(QColor("#94a3b8")))
            painter.drawText(rect, Qt.AlignCenter, f"{self._label} 数据等待中")
            return

        points: list[QPointF] = []
        step = rect.width() / max(1, len(self._values) - 1)
        for index, value in enumerate(self._values):
            clamped = max(-30.0, min(30.0, value))
            x = rect.left() + step * index
            y = rect.center().y() - (clamped / 60.0) * rect.height()
            points.append(QPointF(x, y))

        painter.setPen(QPen(self._color, 3))
        for index in range(1, len(points)):
            painter.drawLine(points[index - 1], points[index])


class ScoreGauge(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._score = 0
        self.setMinimumSize(124, 96)

    def set_score(self, score: int) -> None:
        self._score = max(0, min(100, score))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(16, 8, -16, 6)
        gauge_rect = rect.adjusted(4, 6, -4, -10)

        bg_pen = QPen(QColor("#e7edf5"), 10)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(gauge_rect, 210 * 16, -240 * 16)

        color = QColor("#41be69") if self._score >= 80 else QColor("#2f80ed")
        if self._score < 60:
            color = QColor("#f59e0b")
        value_pen = QPen(color, 10)
        value_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(value_pen)
        painter.drawArc(gauge_rect, 210 * 16, int(-240 * 16 * (self._score / 100)))

        painter.setPen(color)
        font = painter.font()
        font.setPointSize(25)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, str(self._score))


class MainWindow(QMainWindow):
    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("智能颈椎监测系统")
        self.resize(1280, 760)
        self._abnormal_count = 0
        self._was_abnormal = False
        self._alert_active = False
        self._sample_count = 0
        self._pitch_values: list[float] = []
        self._roll_values: list[float] = []

        self.health_score_value = QLabel("--")
        self.posture_value = QLabel("等待数据")
        self.mode_value = QLabel("--")
        self.wear_time_value = QLabel("--")
        self.bluetooth_status_value = QLabel("JDY-24M 模拟")
        self.time_value = QLabel("--")
        self.score_gauge = ScoreGauge()

        self.pitch_value = QLabel("--")
        self.roll_value = QLabel("--")
        self.confidence_value = QLabel("--")
        self.abnormal_count_value = QLabel("0")
        self.last_reminder_value = QLabel("--")
        self.avg_score_value = QLabel("--")
        self.device_signal_value = QLabel("--")
        self.dashboard_pitch_value = QLabel("--")
        self.dashboard_roll_value = QLabel("--")
        self.dashboard_confidence_value = QLabel("--")
        self.dashboard_abnormal_count_value = QLabel("0 次")
        self.stats_abnormal_count_value = QLabel("0 次")
        self.history_total_value = QLabel("--")
        self.history_abnormal_value = QLabel("0 次")
        self.history_avg_score_value = QLabel("--")

        self.receive_button = QPushButton("停止接收")
        self.receive_button.setCheckable(True)
        self.receive_button.setChecked(True)
        self.history_table = QTableWidget(0, 7)
        self.pages = QStackedWidget()
        self.pitch_chart = LineChart("#2f80ed", "Pitch")
        self.roll_chart = LineChart("#36b864", "Roll")
        self.dashboard_pitch_chart = LineChart("#2f80ed", "Pitch")
        self.dashboard_roll_chart = LineChart("#36b864", "Roll")

        self._build_ui()
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._update_clock)
        self._clock.start(1000)
        self._update_clock()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #edf3fa; }
            * { font-family: "Microsoft YaHei", "Segoe UI"; }
            QLabel { color: #172033; font-size: 14px; border: none; }
            QPushButton {
                min-height: 38px;
                padding: 0 18px;
                border: 1px solid #c9d7ea;
                border-radius: 8px;
                background: #ffffff;
                color: #172033;
                font-weight: 700;
            }
            QPushButton:hover { background: #edf6ff; border-color: #60a5fa; }
            QPushButton:checked { background: #1463ff; border-color: #1463ff; color: #ffffff; }
            QPushButton#navButton {
                min-height: 52px;
                text-align: left;
                padding-left: 22px;
                border: none;
                border-radius: 8px;
                background: transparent;
                color: #dbeafe;
                font-size: 17px;
            }
            QPushButton#navButton:checked {
                background: #1463ff;
                color: #ffffff;
            }
            QTableWidget {
                border: 1px solid #d6e0ec;
                border-radius: 8px;
                background: #ffffff;
                alternate-background-color: #f8fbff;
                gridline-color: #e6edf5;
                font-size: 15px;
                selection-background-color: #dbeafe;
            }
            QHeaderView::section {
                background: #eaf2ff;
                color: #1e3a8a;
                border: none;
                border-bottom: 1px solid #d6e0ec;
                padding: 10px;
                font-weight: 700;
            }
            QProgressBar {
                border: none;
            }
            """
        )

        central = QWidget(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), 1)
        self.setCentralWidget(central)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            """
            QFrame#sidebar {
                background: #071b31;
                border: none;
            }
            """
        )
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(14)

        brand = QLabel("智能颈椎监测系统")
        brand.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 800;")
        layout.addWidget(brand)
        layout.addSpacing(28)

        nav_items = [
            ("首页", 0),
            ("实时监测", 1),
            ("历史记录", 2),
            ("设备设置", 3),
        ]
        self.nav_buttons: list[QPushButton] = []
        for text, page_index in nav_items:
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, idx=page_index: self._switch_page(idx))
            layout.addWidget(button)
            self.nav_buttons.append(button)

        self.nav_buttons[0].setChecked(True)
        layout.addStretch(1)
        layout.addWidget(self._sidebar_status())
        return sidebar

    def _sidebar_status(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet(
            """
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border-top: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
            }
            """
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        status = QLabel("蓝牙  已连接")
        status.setStyleSheet("color: #50d579; font-weight: 800;")
        device = QLabel("NeckMonitor-01")
        device.setStyleSheet("color: #ffffff; font-weight: 700;")
        battery = QLabel("电量：--")
        battery.setStyleSheet("color: #b9c7d8;")
        version = QLabel("版本：v1.0.0")
        version.setStyleSheet("color: #8fa3bb;")

        layout.addWidget(status)
        layout.addWidget(device)
        layout.addWidget(battery)
        layout.addSpacing(10)
        layout.addWidget(version)
        return panel

    def _build_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 22, 24, 16)
        layout.setSpacing(18)
        layout.addWidget(self._build_header())

        self.pages.addWidget(self._build_home_page())
        self.pages.addWidget(self._build_realtime_page())
        self.pages.addWidget(self._build_history_page())
        self.pages.addWidget(self._build_settings_page())
        layout.addWidget(self.pages, 1)
        layout.addWidget(self._build_footer())
        return content

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("智能颈椎监测系统")
        title.setStyleSheet("font-size: 28px; font-weight: 900; color: #0d1728;")
        badge = QLabel("蓝牙  设备已连接")
        badge.setStyleSheet(
            "background: #dcecff; color: #1463ff; padding: 9px 16px; "
            "border-radius: 18px; font-weight: 800;"
        )

        self.receive_button.clicked.connect(self._toggle_receiving)
        self.time_value.setStyleSheet("color: #667085; font-size: 15px;")

        layout.addWidget(title)
        layout.addWidget(badge)
        layout.addStretch(1)
        layout.addWidget(self.time_value)
        layout.addWidget(self.receive_button)
        return header

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        top_cards = QHBoxLayout()
        top_cards.setSpacing(16)
        top_cards.addWidget(
            self._summary_card(
                "健康评分",
                self.health_score_value,
                "较昨日 ↑ --",
                "#41be69",
                "gauge",
            )
        )
        top_cards.addWidget(
            self._summary_card(
                "当前状态",
                self.posture_value,
                "持续时间 --",
                "#41be69",
                "text",
            )
        )
        top_cards.addWidget(
            self._summary_card(
                "提醒模式",
                self.mode_value,
                "震动强度：--",
                "#2f80ed",
                "text",
            )
        )
        top_cards.addWidget(
            self._summary_card(
                "今日佩戴时长",
                self.wear_time_value,
                "目标：--",
                "#7c3aed",
                "text",
            )
        )

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._realtime_panel(), 2)
        body.addWidget(self._right_panel(), 1)

        layout.addLayout(top_cards)
        layout.addLayout(body, 1)
        return page

    def _build_realtime_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)
        layout.addWidget(
            self._angle_card("俯仰角 Pitch", self.pitch_value, self.pitch_chart, "#2f80ed"),
            0,
            0,
        )
        layout.addWidget(
            self._angle_card("横滚角 Roll", self.roll_value, self.roll_chart, "#36b864"),
            0,
            1,
        )
        layout.addWidget(
            self._metric_panel("识别置信度", self.confidence_value, "由 STM32U575 计算并通过蓝牙发送"),
            1,
            0,
            1,
            2,
        )
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        top = QHBoxLayout()
        top.addWidget(self._small_stat("累计数据", self.history_total_value))
        top.addWidget(self._small_stat("异常次数", self.history_abnormal_value))
        top.addWidget(self._small_stat("平均评分", self.history_avg_score_value))
        top.addStretch(1)

        self.history_table.setHorizontalHeaderLabels(
            ["时间", "评分", "Pitch", "Roll", "姿态", "模式", "数据源"]
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setShowGrid(False)
        self.history_table.verticalHeader().setDefaultSectionSize(46)

        layout.addLayout(top)
        layout.addWidget(self.history_table, 1)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._metric_panel("设备名称", QLabel("NeckMonitor-01"), "真实蓝牙接入后自动读取"), 0, 0)
        layout.addWidget(self._metric_panel("蓝牙模块", QLabel("JDY-24M"), "当前为模拟数据源"), 0, 1)
        layout.addWidget(self._metric_panel("串口参数", QLabel("--"), "预留波特率、端口号、校验位"), 1, 0)
        layout.addWidget(self._metric_panel("数据格式", QLabel("JSON"), "score/state/pitch/roll/mode"), 1, 1)
        return page

    def _summary_card(
        self,
        title: str,
        value_widget: QLabel,
        hint: str,
        color: str,
        display: str,
    ) -> QWidget:
        card = self._card()
        card.setMinimumHeight(158)
        card.setMaximumHeight(172)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: 900; color: #0d1728;")
        value_widget.setAlignment(Qt.AlignCenter)
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet(
            f"font-size: 30px; font-weight: 900; color: {color}; line-height: 1.05;"
        )
        hint_label = QLabel(hint)
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("color: #667085; font-size: 14px; font-weight: 700;")
        layout.addWidget(title_label)
        if display == "gauge":
            layout.addWidget(self.score_gauge, 1, Qt.AlignCenter)
            value_widget.hide()
        else:
            layout.addStretch(1)
            layout.addWidget(value_widget)
            layout.addStretch(1)
        layout.addWidget(hint_label)
        return card

    def _realtime_panel(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("实时姿态数据")
        title.setStyleSheet("font-size: 18px; font-weight: 900;")
        layout.addWidget(title)

        angles = QHBoxLayout()
        angles.addWidget(
            self._angle_card(
                "俯仰角 Pitch",
                self.dashboard_pitch_value,
                self.dashboard_pitch_chart,
                "#2f80ed",
            )
        )
        angles.addWidget(
            self._angle_card(
                "横滚角 Roll",
                self.dashboard_roll_value,
                self.dashboard_roll_chart,
                "#36b864",
            )
        )
        layout.addLayout(angles, 1)

        bottom = QGridLayout()
        bottom.addWidget(self._compact_data("识别置信度", self.dashboard_confidence_value), 0, 0)
        bottom.addWidget(self._compact_data("异常计数", self.dashboard_abnormal_count_value), 0, 1)
        bottom.addWidget(self._compact_data("最后提醒", self.last_reminder_value), 0, 2)
        layout.addLayout(bottom)
        return card

    def _right_panel(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._metric_panel("姿态状态指示", QLabel("正常 / 低头 / 左倾 / 右倾"), "图形化状态指示预留"))
        layout.addWidget(self._stats_panel())
        layout.addWidget(self._device_panel())
        return wrapper

    def _angle_card(self, title: str, value_widget: QLabel, chart: LineChart, color: str) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: 800;")
        value_widget.setAlignment(Qt.AlignCenter)
        value_widget.setStyleSheet(f"font-size: 38px; font-weight: 900; color: {color};")
        range_label = QLabel("正常范围：预留")
        range_label.setAlignment(Qt.AlignCenter)
        range_label.setStyleSheet("color: #667085;")
        layout.addWidget(title_label)
        layout.addWidget(value_widget)
        layout.addWidget(range_label)
        layout.addWidget(chart)
        return card

    def _stats_panel(self) -> QWidget:
        card = self._card()
        layout = QGridLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        title = QLabel("今日数据统计")
        title.setStyleSheet("font-size: 18px; font-weight: 900;")
        layout.addWidget(title, 0, 0, 1, 2)
        rows = [
            ("异常次数", self.stats_abnormal_count_value),
            ("平均健康评分", self.avg_score_value),
            ("最长低头时间", QLabel("--")),
            ("久坐提醒次数", QLabel("--")),
        ]
        for row, (name, value) in enumerate(rows, start=1):
            name_label = QLabel(name)
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value.setStyleSheet("font-size: 16px; font-weight: 800;")
            layout.addWidget(name_label, row, 0)
            layout.addWidget(value, row, 1)
        return card

    def _device_panel(self) -> QWidget:
        card = self._card()
        layout = QGridLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        title = QLabel("设备信息")
        title.setStyleSheet("font-size: 18px; font-weight: 900;")
        layout.addWidget(title, 0, 0, 1, 2)
        rows = [
            ("设备名称", "NeckMonitor-01"),
            ("固件版本", "--"),
            ("蓝牙信号", "--"),
            ("电量", "--"),
        ]
        for row, (name, value) in enumerate(rows, start=1):
            layout.addWidget(QLabel(name), row, 0)
            value_label = QLabel(value)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setStyleSheet("font-weight: 800;")
            if name == "蓝牙信号":
                self.device_signal_value = value_label
            layout.addWidget(value_label, row, 1)
        return card

    def _metric_panel(self, title: str, value_widget: QLabel, hint: str) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: 900;")
        value_widget.setStyleSheet("font-size: 24px; font-weight: 900; color: #1463ff;")
        hint_label = QLabel(hint)
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #667085;")
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(value_widget)
        layout.addWidget(hint_label)
        return card

    def _compact_data(self, title: str, value_widget: QLabel) -> QWidget:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #f8fbff; border: 1px solid #edf2f7; border-radius: 8px; }"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #172033; font-weight: 800;")
        value_widget.setAlignment(Qt.AlignCenter)
        value_widget.setStyleSheet("font-size: 22px; font-weight: 900; color: #1463ff;")
        layout.addWidget(title_label)
        layout.addWidget(value_widget)
        return card

    def _small_stat(self, title: str, value_widget: QLabel) -> QWidget:
        card = self._card()
        card.setFixedHeight(86)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #667085; font-weight: 800;")
        value_widget.setStyleSheet("font-size: 24px; font-weight: 900; color: #1463ff;")
        layout.addWidget(title_label)
        layout.addWidget(value_widget)
        return card

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(6, 0, 6, 0)
        left = QLabel("数据更新频率：1.0s")
        right = QLabel("数据来源：STM32 + JDY-24M 模拟设备")
        left.setStyleSheet("color: #667085;")
        right.setStyleSheet("color: #667085;")
        layout.addWidget(left)
        layout.addStretch(1)
        layout.addWidget(right)
        return footer

    def _card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card.setStyleSheet(
            """
            QFrame#card {
                background: #ffffff;
                border: 1px solid #d6e0ec;
                border-radius: 10px;
            }
            """
        )
        return card

    def _switch_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

    def update_sample(self, sample: NeckSensorSample, sample_count: int) -> None:
        abnormal = sample.state != "正常"
        if abnormal and not self._was_abnormal:
            self._abnormal_count += 1
        if sample.alert and not self._alert_active:
            self.last_reminder_value.setText(sample.timestamp.strftime("%H:%M:%S"))
        self._was_abnormal = abnormal
        self._alert_active = sample.alert

        self._sample_count = sample_count
        self._pitch_values.append(sample.pitch)
        self._roll_values.append(sample.roll)
        self._pitch_values = self._pitch_values[-40:]
        self._roll_values = self._roll_values[-40:]

        self.health_score_value.setText(str(sample.score))
        self.score_gauge.set_score(sample.score)
        self.posture_value.setText(sample.state)
        self.mode_value.setText(self._display_mode(sample.mode))
        self.wear_time_value.setText("--")
        self.abnormal_count_value.setText(f"{self._abnormal_count} 次")
        self.dashboard_abnormal_count_value.setText(f"{self._abnormal_count} 次")
        self.stats_abnormal_count_value.setText(f"{self._abnormal_count} 次")
        self.history_abnormal_value.setText(f"{self._abnormal_count} 次")
        self.bluetooth_status_value.setText("JDY-24M 接收中")
        self.pitch_value.setText(f"{sample.pitch:.1f}°")
        self.roll_value.setText(f"{sample.roll:.1f}°")
        self.dashboard_pitch_value.setText(f"{sample.pitch:.1f}°")
        self.dashboard_roll_value.setText(f"{sample.roll:.1f}°")
        confidence_text = (
            "--" if sample.confidence is None else f"{sample.confidence * 100:.1f}%"
        )
        self.confidence_value.setText(confidence_text)
        self.dashboard_confidence_value.setText(confidence_text)
        self.avg_score_value.setText(f"{sample.score} 分")
        self.history_avg_score_value.setText(f"{sample.score} 分")
        self.history_total_value.setText(f"{sample_count} 条")
        self.device_signal_value.setText("--")

        self.pitch_chart.set_values(self._pitch_values)
        self.roll_chart.set_values(self._roll_values)
        self.dashboard_pitch_chart.set_values(self._pitch_values)
        self.dashboard_roll_chart.set_values(self._roll_values)
        self._append_history(sample)

    def _append_history(self, sample: NeckSensorSample) -> None:
        self.history_table.insertRow(0)
        values = [
            sample.timestamp.strftime("%H:%M:%S"),
            str(sample.score),
            f"{sample.pitch:.1f}",
            f"{sample.roll:.1f}",
            sample.state,
            sample.mode,
            "JDY-24M",
        ]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor("#d92d20") if sample.state != "正常" else QColor("#1a9f55"))
            if column in (1, 4):
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.history_table.setItem(0, column, item)

        while self.history_table.rowCount() > 120:
            self.history_table.removeRow(self.history_table.rowCount() - 1)

    @staticmethod
    def _display_mode(mode: str) -> str:
        mode_names = {
            "0": "普通模式",
            "NORMAL": "普通模式",
            "1": "静音模式",
            "SILENT": "静音模式",
            "2": "强提醒模式",
            "STRONG": "强提醒模式",
        }
        if "SIM" in mode.upper():
            return "普通模式"
        return mode_names.get(mode.upper(), mode.replace("_", " "))

    def _toggle_receiving(self) -> None:
        if self.receive_button.isChecked():
            self.receive_button.setText("停止接收")
            self.bluetooth_status_value.setText("JDY-24M 接收中")
            self.start_requested.emit()
            return

        self.receive_button.setText("开始接收")
        self.bluetooth_status_value.setText("已停止")
        self.stop_requested.emit()

    def update_bluetooth_status(self, connected: bool) -> None:
        status = "JDY-24M 接收中" if connected else "已停止"
        self.bluetooth_status_value.setText(status)
        self.bluetooth_status_value.setToolTip("")
        self.receive_button.setChecked(connected)
        self.receive_button.setText("停止接收" if connected else "开始接收")

    def show_data_error(self, message: str) -> None:
        self.bluetooth_status_value.setText("数据格式错误")
        self.bluetooth_status_value.setToolTip(message)

    def _update_clock(self) -> None:
        self.time_value.setText(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
