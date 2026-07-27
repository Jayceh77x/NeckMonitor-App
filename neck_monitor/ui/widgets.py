from __future__ import annotations

import math
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
    QTransform,
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
        ) or any(token in state for token in ("低头", "左倾", "右倾", "侧倾")):
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

        score_font = QFont(painter.font())
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

        caption_font = QFont(painter.font())
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
    """Compact real-time line chart with grid, thresholds and soft area fill."""

    def __init__(self, color: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._label = label
        self._values: list[float] = []
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_values(self, values: list[float]) -> None:
        self._values = list(values[-40:])
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        plot_rect = QRectF(self.rect()).adjusted(38, 12, -12, -24)
        if plot_rect.width() <= 1 or plot_rect.height() <= 1:
            return

        painter.setPen(QPen(QColor("#e7edf5"), 1, Qt.DashLine))
        for value in (30, 15, 0, -15, -30):
            y = self._value_to_y(value, plot_rect)
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

        label_font = QFont(painter.font())
        label_font.setPointSize(8)
        painter.setFont(label_font)
        painter.setPen(QColor("#8492a6"))
        for value in (30, 0, -30):
            y = self._value_to_y(value, plot_rect)
            label_rect = QRectF(0, y - 9, 32, 18)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, f"{value}°")

        normal_fill = QColor(self._color)
        normal_fill.setAlpha(12)
        normal_top = self._value_to_y(15, plot_rect)
        normal_bottom = self._value_to_y(-15, plot_rect)
        painter.fillRect(
            QRectF(
                plot_rect.left(),
                normal_top,
                plot_rect.width(),
                normal_bottom - normal_top,
            ),
            normal_fill,
        )

        if len(self._values) < 2:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(plot_rect, Qt.AlignCenter, f"{self._label} 数据等待中")
            return

        points: list[QPointF] = []
        step = plot_rect.width() / max(1, len(self._values) - 1)
        for index, value in enumerate(self._values):
            x = plot_rect.left() + step * index
            y = self._value_to_y(value, plot_rect)
            points.append(QPointF(x, y))

        line_path = QPainterPath(points[0])
        for point in points[1:]:
            line_path.lineTo(point)

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

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(points[-1], 3.5, 3.5)

        painter.setPen(QColor("#94a3b8"))
        painter.drawText(
            QRectF(plot_rect.left(), plot_rect.bottom() + 5, plot_rect.width(), 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            "较早",
        )
        painter.drawText(
            QRectF(plot_rect.left(), plot_rect.bottom() + 5, plot_rect.width(), 16),
            Qt.AlignRight | Qt.AlignVCenter,
            "当前",
        )

    @staticmethod
    def _value_to_y(value: float, rect: QRectF) -> float:
        clamped = max(-30.0, min(30.0, float(value)))
        return rect.center().y() - (clamped / 60.0) * rect.height()


class PostureGauge(QWidget):
    """Segmented posture-state indicator driven only by the STM32 state field."""

    _LABELS = ("仰头", "左倾", "正常", "右倾", "低头")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = "等待数据"
        head_neck_pixmap = QPixmap(
            str(Path(__file__).resolve().parent / "assets" / "posture" / "头部轮廓.png")
        )
        self._head_neck_pixmap = head_neck_pixmap.transformed(
            QTransform().scale(-1.0, 1.0),
            Qt.SmoothTransformation,
        )
        self.setMinimumHeight(140)
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
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        width = max(150.0, min(self.width() - 76.0, 340.0))
        arc_height = max(62.0, min(width * 0.42, self.height() - 62.0))
        arc_rect = QRectF((self.width() - width) / 2, 36, width, arc_height)
        active_index = self._active_index(self._state)
        segment_span = -40
        gap = 4
        drawn_span = segment_span + gap

        for index in range(5):
            color = QColor("#dfe5ec")
            if index == active_index:
                color = QColor("#31b968") if index == 2 else QColor("#f59e0b")
            pen = QPen(color, 9)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            start = 200 - index * 44
            painter.drawArc(arc_rect, start * 16, drawn_span * 16)

        label_font = QFont(painter.font())
        label_font.setPointSize(8)
        label_font.setWeight(QFont.DemiBold)
        painter.setFont(label_font)
        center = arc_rect.center()
        label_radius_x = arc_rect.width() / 2 + 20
        label_radius_y = arc_rect.height() / 2 + 15
        for index, label in enumerate(self._LABELS):
            segment_start = 200 - index * 44
            angle = math.radians(segment_start + drawn_span / 2)
            x = center.x() + math.cos(angle) * label_radius_x
            y = center.y() - math.sin(angle) * label_radius_y
            if index == 0:
                x -= 10
            elif index == len(self._LABELS) - 1:
                x += 10
            label_width = 48.0
            label_height = 22.0
            label_x = max(0.0, min(x - label_width / 2, self.width() - label_width))
            label_y = max(2.0, min(y - label_height / 2, self.height() - label_height - 28.0))
            label_color = QColor("#758195")
            if index == active_index:
                label_color = QColor("#31b968") if active_index == 2 else QColor("#f59e0b")
            painter.setPen(label_color)
            painter.drawText(
                QRectF(label_x, label_y, label_width, label_height),
                Qt.AlignCenter,
                label,
            )

        if not self._head_neck_pixmap.isNull():
            image_height = max(46, min(70, self.height() - 70))
            scaled = self._head_neck_pixmap.scaled(
                int(image_height),
                int(image_height),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            image_bottom = self.height() - 30
            image_rect = QRectF(
                center.x() - scaled.width() / 2,
                image_bottom - scaled.height(),
                scaled.width(),
                scaled.height(),
            )
            painter.drawPixmap(image_rect, scaled, QRectF(scaled.rect()))

        state_color = QColor("#31b968") if active_index == 2 else QColor("#f59e0b")
        if active_index < 0:
            state_color = QColor("#758195")
        state_font = QFont(painter.font())
        state_font.setPointSize(10)
        state_font.setWeight(QFont.Bold)
        painter.setFont(state_font)
        painter.setPen(state_color)
        painter.drawText(
            QRectF(8, self.height() - 27, self.width() - 16, 24),
            Qt.AlignCenter,
            self._state,
        )

    @staticmethod
    def _active_index(state: str) -> int:
        normalized = state.upper()
        if "NORMAL" in normalized or "正常" in state:
            return 2
        if "HEAD_UP" in normalized or "仰头" in state:
            return 0
        if "TILT_LEFT" in normalized or "左倾" in state:
            return 1
        if "TILT_RIGHT" in normalized or "右倾" in state or "侧倾" in state:
            return 3
        if "HEAD_DOWN" in normalized or "低头" in state:
            return 4
        return -1
