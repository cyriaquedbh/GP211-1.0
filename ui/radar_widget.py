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
        self._compteur_clignotement = 0

    def paintEvent(self, event):
        self._compteur_clignotement += 1
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._dessiner_decor(painter)
        self._dessiner_piste(painter)
        self._dessiner_vent(painter)
        self._dessiner_avions(painter)

    def _dessiner_decor(self, painter):
        """Anneaux de distance + rose des caps, pour un rendu 'vrai scope radar'."""
        cx, cy = self.engine.centre()
        painter.save()
        painter.translate(cx, cy)

        painter.setPen(QPen(QColor(0, 90, 0), 1, Qt.DotLine))
        for rayon in (100, 200, 290):
            painter.drawEllipse(QPointF(0, 0), rayon, rayon)

        painter.setPen(QPen(QColor(0, 130, 0), 1))
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1, y1 = 280 * math.sin(rad), -280 * math.cos(rad)
            x2, y2 = 292 * math.sin(rad), -292 * math.cos(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        font = painter.font()
        font.setPixelSize(11)
        painter.setFont(font)
        painter.setPen(QColor(0, 200, 0))
        for angle, lettre in ((0, "N"), (90, "E"), (180, "S"), (270, "O")):
            rad = math.radians(angle)
            x, y = 265 * math.sin(rad), -265 * math.cos(rad)
            painter.drawText(QPointF(x - 5, y + 5), lettre)

        painter.restore()

    def _dessiner_piste(self, painter):
        cx, cy = self.engine.centre()
        piste = self.engine.piste_active
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(piste.cap)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(45, 45, 45))
        painter.drawRect(-piste.largeur // 2, -piste.longueur // 2, piste.largeur, piste.longueur)

        painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
        painter.drawLine(0, -piste.longueur // 2 + 10, 0, piste.longueur // 2 - 10)

        painter.setPen(QPen(QColor(255, 255, 255), 3))
        for bord in (-piste.longueur // 2, piste.longueur // 2):
            signe = 1 if bord < 0 else -1
            for i in range(-15, 16, 6):
                painter.drawLine(i, bord, i, bord + signe * 12)

        font = painter.font()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 0)))
        painter.drawText(-25, -piste.longueur // 2 - 10, piste.nom)
        painter.restore()

    def _dessiner_vent(self, painter):
        cx, cy = self.engine.centre()
        vent = self.engine.vent
        origine = QPointF(cx + 220, cy - 220)

        painter.save()
        painter.translate(origine)
        painter.rotate(vent.direction)
        painter.setPen(QPen(QColor(0, 220, 255), 2))
        painter.drawLine(0, -20, 0, 20)
        painter.drawLine(0, -20, -6, -10)
        painter.drawLine(0, -20, 6, -10)
        painter.restore()

        painter.setPen(QColor(0, 220, 255))
        painter.drawText(int(origine.x()) - 35, int(origine.y()) + 35,
                          f"Vent {vent.direction:03d}°/{vent.vitesse}km/h")

    def _dessiner_avions(self, painter):
        clignote_visible = (self._compteur_clignotement // 5) % 2 == 0
        for avion in self.engine.avions:
            if avion.en_alerte and clignote_visible:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 0, 0, 90))
                painter.drawEllipse(QPointF(avion.x, avion.y), 18, 18)

            painter.save()
            painter.translate(avion.x, avion.y)
            painter.rotate(avion.cap - 90)
            poly = QPolygonF([QPointF(12, 0), QPointF(-8, -10), QPointF(-4, 0), QPointF(-8, 10)])
            if avion.en_alerte:
                couleur = QColor(255, 0, 0)
            elif avion.selected:
                couleur = QColor(255, 150, 0)
            else:
                couleur = QColor(50, 255, 255)
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