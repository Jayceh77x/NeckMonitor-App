from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QFrame, QPushButton, QSizePolicy, QWidget


class CardFrame(QFrame):
    """Reusable dashboard card with a quiet, consistent visual surface."""

    def __init__(self, parent: QWidget | None = None, *, muted: bool = False) -> None:
        super().__init__(parent)
        self.setObjectName("mutedCard" if muted else "appCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class AppButton(QPushButton):
    """Shared button roles keep navigation and actions visually consistent."""

    def __init__(
        self,
        text: str,
        parent: QWidget | None = None,
        *,
        role: str = "secondary",
    ) -> None:
        super().__init__(text, parent)
        self.setProperty("role", role)
        if role == "navigation":
            self.setObjectName("navButton")
            self.setCheckable(True)
        elif role == "primary":
            self.setObjectName("primaryButton")


class PostureImage(QWidget):
    """State-driven posture artwork with a safe fallback for missing assets."""

    _ASSET_NAMES = {
        "normal": "正常坐姿.png",
        "head_up": "后仰.png",
        "shared_abnormal": "低头.png",
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        asset_dir: str | Path | None = None,
    ) -> None:
        super().__init__(parent)
        self._state = "等待数据"
        self._asset_dir = (
            Path(asset_dir)
            if asset_dir is not None
            else Path(__file__).resolve().parent / "assets" / "posture"
        )
        self._pixmaps = {
            key: QPixmap(str(self._asset_dir / filename))
            for key, filename in self._ASSET_NAMES.items()
        }
        self.setMinimumSize(84, 54)
        self.setMaximumHeight(64)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_state(self, state: str) -> None:
        state = str(state or "等待数据")
        if state == self._state:
            return
        self._state = state
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        backdrop_size = min(62.0, float(self.height() - 2), float(self.width()))
        backdrop = QRectF(
            (self.width() - backdrop_size) / 2,
            (self.height() - backdrop_size) / 2,
            backdrop_size,
            backdrop_size,
        )
        asset_key = self._asset_key(self._state)
        backdrop_color = "#effaf3" if asset_key == "normal" else "#fff6e5"
        if not asset_key:
            backdrop_color = "#f3f6fa"
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(backdrop_color))
        painter.drawEllipse(backdrop)

        pixmap = self._pixmaps.get(asset_key)
        if pixmap is None or pixmap.isNull():
            return

        available = backdrop.adjusted(5, 6, -5, -5)
        scaled = pixmap.scaled(
            int(available.width()),
            int(available.height()),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        target = QRectF(
            available.center().x() - scaled.width() / 2,
            available.center().y() - scaled.height() / 2,
            scaled.width(),
            scaled.height(),
        )
        painter.drawPixmap(target, scaled, QRectF(scaled.rect()))

    @staticmethod
    def _asset_key(state: str) -> str:
        normalized = state.upper()
        if "NORMAL" in normalized or "正常" in state:
            return "normal"
        if "HEAD_UP" in normalized or "仰头" in state or "后仰" in state:
            return "head_up"
        if any(
            token in normalized
            for token in ("HEAD_DOWN", "TILT_LEFT", "TILT_RIGHT", "TILT")
        ) or any(token in state for token in ("低头", "左倾", "右倾", "侧倾", "浣庡ご")):
            return "shared_abnormal"
        return ""


class ScoreGauge(QWidget):
    """Animated-data-ready circular score gauge drawn at any DPI."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._score = 0
        self.setMinimumSize(118, 92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_score(self, score: int) -> None:
        bounded_score = max(0, min(100, int(score)))
        if bounded_score == self._score:
            return
        self._score = bounded_score
        self.update()

    @staticmethod
    def _score_color(score: int) -> QColor:
        if score >= 80:
            return QColor("#31b968")
        if score >= 60:
            return QColor("#2f80ed")
        return QColor("#f59e0b")

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width() - 24, self.height() - 10)
        gauge_rect = QRectF(
            (self.width() - side) / 2,
            (self.height() - side) / 2 - 1,
            side,
            side,
        )
        line_width = max(8.0, side * 0.085)
        start_angle = 220 * 16
        span_angle = -280 * 16

        background_pen = QPen(QColor("#e8edf4"), line_width)
        background_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(background_pen)
        painter.drawArc(gauge_rect, start_angle, span_angle)

        color = self._score_color(self._score)
        value_pen = QPen(color, line_width)
        value_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(value_pen)
        painter.drawArc(
            gauge_rect,
            start_angle,
            int(span_angle * (self._score / 100.0)),
        )

        score_font = QFont("Microsoft YaHei")
        score_font.setPointSize(max(17, int(side * 0.22)))
        score_font.setWeight(QFont.Bold)
        painter.setFont(score_font)
        painter.setPen(color)
        score_rect = QRectF(
            gauge_rect.left(),
            gauge_rect.center().y() - side * 0.25,
            gauge_rect.width(),
            side * 0.34,
        )
        painter.drawText(score_rect, Qt.AlignCenter, str(self._score))

        caption_font = QFont("Microsoft YaHei")
        caption_font.setPointSize(max(8, int(side * 0.08)))
        caption_font.setWeight(QFont.DemiBold)
        painter.setFont(caption_font)
        caption = "优秀" if self._score >= 80 else "良好" if self._score >= 60 else "需关注"
        caption_rect = QRectF(
            gauge_rect.left(),
            gauge_rect.center().y() + side * 0.08,
            gauge_rect.width(),
            max(18.0, side * 0.20),
        )
        painter.drawText(
            caption_rect,
            Qt.AlignCenter,
            caption,
        )


class LineChart(QWidget):
    """Auto-scaling real-time line chart with timestamped x-axis labels."""

    _MAX_POINTS = 180

    def __init__(self, color: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._label = label
        self._values: list[float] = []
        self._timestamps: list[datetime] = []
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_values(
        self,
        values: list[float],
        timestamps: list[datetime] | None = None,
    ) -> None:
        self._values = list(values[-self._MAX_POINTS :])
        self._timestamps = list((timestamps or [])[-len(self._values) :])
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        plot_rect = QRectF(self.rect()).adjusted(46, 12, -14, -28)
        if plot_rect.width() <= 1 or plot_rect.height() <= 1:
            return

        if len(self._values) < 2:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(plot_rect, Qt.AlignCenter, f"{self._label} 数据等待中")
            return

        lower_bound, upper_bound, ticks = self._build_axis(self._values)

        painter.setPen(QPen(QColor("#e7edf5"), 1, Qt.DashLine))
        for value in ticks:
            y = self._value_to_y(value, plot_rect, lower_bound, upper_bound)
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

        label_font = QFont("Microsoft YaHei")
        label_font.setPointSize(8)
        painter.setFont(label_font)
        painter.setPen(QColor("#8492a6"))
        for value in ticks:
            y = self._value_to_y(value, plot_rect, lower_bound, upper_bound)
            label_rect = QRectF(0, y - 9, 42, 18)
            painter.drawText(
                label_rect,
                Qt.AlignRight | Qt.AlignVCenter,
                f"{self._format_axis_value(value)}°",
            )

        points: list[QPointF] = []
        step = plot_rect.width() / max(1, len(self._values) - 1)
        for index, value in enumerate(self._values):
            x = plot_rect.left() + step * index
            y = self._value_to_y(value, plot_rect, lower_bound, upper_bound)
            points.append(QPointF(x, y))

        line_path = self._smooth_path(points, plot_rect)

        area_path = QPainterPath(line_path)
        area_path.lineTo(points[-1].x(), plot_rect.bottom())
        area_path.lineTo(points[0].x(), plot_rect.bottom())
        area_path.closeSubpath()

        gradient = QLinearGradient(0, plot_rect.top(), 0, plot_rect.bottom())
        fill_color = QColor(self._color)
        fill_color.setAlpha(68)
        gradient.setColorAt(0.0, fill_color)
        transparent = QColor(self._color)
        transparent.setAlpha(0)
        gradient.setColorAt(1.0, transparent)
        painter.fillPath(area_path, gradient)

        line_pen = QPen(self._color, 2.4)
        line_pen.setCapStyle(Qt.RoundCap)
        line_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(line_pen)
        painter.drawPath(line_path)

        self._draw_sample_points(painter, points)

        self._draw_time_labels(painter, plot_rect)

    @staticmethod
    def _value_to_y(value: float, rect: QRectF, lower_bound: float, upper_bound: float) -> float:
        span = max(1e-6, upper_bound - lower_bound)
        ratio = (float(value) - lower_bound) / span
        return rect.bottom() - ratio * rect.height()

    @staticmethod
    def _build_axis(values: list[float]) -> tuple[float, float, list[float]]:
        axis_limit = max(abs(value) for value in values)
        axis_limit = max(axis_limit, 1.0)
        ticks = [
            -axis_limit,
            -axis_limit / 2,
            0.0,
            axis_limit / 2,
            axis_limit,
        ]
        return -axis_limit, axis_limit, ticks

    @staticmethod
    def _format_axis_value(value: float) -> str:
        if abs(value) >= 10 or abs(value - round(value)) < 0.05:
            return str(int(round(value)))
        return f"{value:.1f}"

    @staticmethod
    def _smooth_path(points: list[QPointF], plot_rect: QRectF) -> QPainterPath:
        if len(points) < 3:
            path = QPainterPath(points[0])
            for point in points[1:]:
                path.lineTo(point)
            return path

        def clamp_y(value: float) -> float:
            return max(plot_rect.top(), min(value, plot_rect.bottom()))

        path = QPainterPath(points[0])
        for index in range(len(points) - 1):
            p0 = points[index - 1] if index > 0 else points[index]
            p1 = points[index]
            p2 = points[index + 1]
            p3 = points[index + 2] if index + 2 < len(points) else p2

            c1 = QPointF(
                p1.x() + (p2.x() - p0.x()) / 6.0,
                clamp_y(p1.y() + (p2.y() - p0.y()) / 6.0),
            )
            c2 = QPointF(
                p2.x() - (p3.x() - p1.x()) / 6.0,
                clamp_y(p2.y() - (p3.y() - p1.y()) / 6.0),
            )
            path.cubicTo(c1, c2, p2)
        return path

    def _draw_sample_points(self, painter: QPainter, points: list[QPointF]) -> None:
        if not points:
            return

        base_brush = QColor(self._color)
        base_brush.setAlpha(200)
        edge_pen = QPen(base_brush.darker(115), 0.8)
        painter.setPen(edge_pen)
        painter.setBrush(base_brush)
        for point in points[:-1]:
            painter.drawEllipse(point, 1.6, 1.6)

        highlight_brush = QColor(self._color)
        highlight_brush.setAlpha(255)
        painter.setPen(QPen(highlight_brush.darker(110), 1.0))
        painter.setBrush(highlight_brush)
        painter.drawEllipse(points[-1], 2.5, 2.5)

    def _draw_time_labels(self, painter: QPainter, plot_rect: QRectF) -> None:
        if not self._timestamps:
            return

        latest_time = self._timestamps[-1].replace(second=0, microsecond=0)
        slots = [
            (plot_rect.left(), latest_time - timedelta(minutes=2)),
            (plot_rect.center().x(), latest_time - timedelta(minutes=1)),
            (plot_rect.right(), latest_time),
        ]

        painter.setPen(QColor("#94a3b8"))
        label_width = 72.0
        for x, timestamp in slots:
            label_x = max(plot_rect.left(), min(x - label_width / 2, plot_rect.right() - label_width))
            label_rect = QRectF(label_x, plot_rect.bottom() + 6, label_width, 18)
            painter.drawText(
                label_rect,
                Qt.AlignCenter,
                timestamp.strftime("%H:%M"),
            )


class PostureGauge(QWidget):
    """Compact single-state posture indicator driven only by the STM32 state field."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = "等待数据"
        self.setMinimumHeight(136)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_state(self, state: str) -> None:
        state = str(state or "等待数据")
        if state == self._state:
            return
        self._state = state
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        active_state = self._active_state(self._state)
        if active_state == "normal":
            self._draw_status_block(painter, "正常", "#31b968")
        elif active_state == "abnormal":
            self._draw_status_block(painter, "姿势异常", "#f59e0b")
        else:
            self._draw_status_block(painter, "等待数据", "#758195")

    @staticmethod
    def _active_state(state: str) -> str:
        normalized = state.upper()
        if "NORMAL" in normalized or "正常" in state or "良好" in state:
            return "normal"
        if any(
            token in normalized
            for token in ("HEAD_DOWN", "HEAD_UP", "TILT_LEFT", "TILT_RIGHT", "TILT")
        ) or any(
            token in state
            for token in ("低头", "仰头", "后仰", "左倾", "右倾", "侧倾", "异常", "浣庡ご")
        ):
            return "abnormal"
        return "unknown"

    @staticmethod
    def _draw_status_block(
        painter: QPainter,
        label: str,
        color: str,
    ) -> None:
        base_color = QColor(color)
        viewport_rect = QRectF(painter.viewport()).adjusted(8, 8, -8, -8)
        rect = QRectF(
            0,
            0,
            viewport_rect.width() * 0.70,
            viewport_rect.height() * 0.70,
        )
        rect.moveCenter(viewport_rect.center())

        border = QColor(base_color)
        border.setAlpha(230)
        background = QColor(base_color)
        background.setAlpha(20)
        painter.setPen(QPen(border, 2.4))
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 10, 10)

        label_font = QFont("Microsoft YaHei")
        label_font.setPointSize(max(16, min(26, int(rect.height() * 0.26))))
        label_font.setWeight(QFont.Black)
        painter.setFont(label_font)
        painter.setPen(base_color)
        painter.drawText(rect, Qt.AlignCenter, label)
