import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF


class RadarWidget(QWidget):
    def __init__(self, engine, on_avion_clicked):
        super().__init__()
        self.engine = engine
        self.on_avion_clicked = on_avion_clicked
        self.setMinimumSize(600, 600)
        self.setStyleSheet("background-color: #001100;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._dessiner_piste(painter)
        self._dessiner_avions(painter)

    def _dessiner_piste(self, painter):
        cx, cy = self.engine.centre()
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.engine.piste_active.cap)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(50, 50, 50))
        painter.drawRect(-20, -150, 40, 300)

        painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
        painter.drawLine(0, -140, 0, 140)

        font = painter.font()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 0)))
        painter.drawText(-25, -160, self.engine.piste_active.nom)
        painter.restore()

    def _dessiner_avions(self, painter):
        for avion in self.engine.avions:
            painter.save()
            painter.translate(avion.x, avion.y)
            painter.rotate(avion.cap - 90)
            poly = QPolygonF([QPointF(12, 0), QPointF(-8, -10), QPointF(-4, 0), QPointF(-8, 10)])
            couleur = QColor(255, 50, 50) if avion.selected else QColor(50, 255, 255)
            painter.setBrush(QBrush(couleur))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawPolygon(poly)
            painter.restore()

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(avion.x + 10), int(avion.y - 10),
                              f"{avion.name} ({int(avion.altitude)}m)")

    def mousePressEvent(self, event):
        click_x, click_y = event.position().x(), event.position().y()
        for avion in self.engine.avions:
            if math.hypot(avion.x - click_x, avion.y - click_y) < 15:
                self.on_avion_clicked(avion)
                break