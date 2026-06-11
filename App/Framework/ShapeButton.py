import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF, QPainterPath
from PySide6.QtCore import QRectF, QPointF, QSize

SHAPE_COLORS = {
    'black':  QColor(0,   0,   0),
    'white':  QColor(255, 255, 255),
    'yellow': QColor(255, 210, 0),
    'blue':   QColor(30,  80,  200),
}

class ShapeButton(QWidget):
    """Renders a geometric shape in a given colour. Fires callback(shape, color) on click.

    Set stim_visible=False to make the widget transparent and non-interactive
    (used for error-reduced trials where one side has no stimulus).
    """

    def __init__(self, shape: str, color: str, size: int = 200,
                 callback=None, parent=None):
        super().__init__(parent)
        self.shape = shape      # 'triangle' | 'circle' | 'star' | 'square'
        self.color = color      # 'black' | 'white' | 'yellow' | 'blue'
        self._size = size
        self._callback = callback
        self.stim_visible = True
        self.setFixedSize(size, size)

    def sizeHint(self):
        return QSize(self._size, self._size)

    def paintEvent(self, event):
        if not self.stim_visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        fill    = SHAPE_COLORS.get(self.color, QColor(0, 0, 0))
        outline = QColor(0, 0, 0)
        pen_w   = max(3, self._size // 50)
        painter.setPen(QPen(outline, pen_w))
        painter.setBrush(fill)

        s = self._size
        m = s * 0.12
        d = s - 2 * m   # drawable region size

        if self.shape == 'circle':
            painter.drawEllipse(QRectF(m, m, d, d))

        elif self.shape == 'square':
            painter.drawRect(QRectF(m, m, d, d))

        elif self.shape == 'triangle':
            poly = QPolygonF([
                QPointF(s / 2, m),
                QPointF(s - m, s - m),
                QPointF(m,     s - m),
            ])
            painter.drawPolygon(poly)

        elif self.shape == 'cross':
            cx, cy = s / 2, s / 2
            bar = d * 0.28
            painter.drawRect(QRectF(cx - bar / 2, m, bar, d))
            painter.drawRect(QRectF(m, cy - bar / 2, d, bar))

        elif self.shape == 'star':
            cx, cy   = s / 2, s / 2
            outer_r  = d / 2
            inner_r  = outer_r * 0.38
            path = QPainterPath()
            pts = []
            for i in range(10):
                r     = outer_r if i % 2 == 0 else inner_r
                angle = math.radians(-90 + i * 36)
                pts.append(QPointF(cx + r * math.cos(angle),
                                   cy + r * math.sin(angle)))
            path.moveTo(pts[0])
            for p in pts[1:]:
                path.lineTo(p)
            path.closeSubpath()
            painter.drawPath(path)

    def setStimVisible(self, visible: bool):
        self.stim_visible = visible
        self.update()

    def mousePressEvent(self, event):
        if self.stim_visible and self._callback:
            self._callback(self.shape, self.color)
        super().mousePressEvent(event)
