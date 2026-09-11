import math
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QFont
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel


class CockpitWidget(QDialog):
    """Fenêtre simulant la vue cockpit du pilote lors de l'approche et de l'atterrissage."""

    def __init__(self, avion, aeroport, parent=None):
        super().__init__(parent)
        self.avion = avion
        self.aeroport = aeroport

        self.setWindowTitle(f"Vue Cockpit — {avion.name}")
        self.resize(800, 500)
        self.setStyleSheet("background-color: #05080c;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # 1. Calcul de l'attitude (Horizon artificiel & Pitch)
        pitch = min(30.0, max(-30.0, (self.avion.altitude - 1000) / 100))
        horizon_y = cy + pitch * 3

        # Ciel
        painter.fillRect(0, 0, w, int(horizon_y), QColor(15, 23, 42))

        # Sol / Décor
        painter.fillRect(0, int(horizon_y), w, int(h - horizon_y), QColor(20, 30, 20))

        # Ligne d'horizon
        painter.setPen(QPen(QColor(56, 189, 248, 180), 2))
        painter.drawLine(0, int(horizon_y), w, int(horizon_y))

        # 2. Rendu Perspective de la Piste (Perspective simplifiée)
        piste = self.avion.piste_visee
        if piste is not None:
            # Facteur d'approche basé sur l'altitude
            factor = max(0.05, min(1.0, 1.0 - (self.avion.altitude / 3000)))
            rw_width_top = 20 * factor
            rw_width_bot = 220 * factor
            rw_height = (h - horizon_y) * factor

            top_y = horizon_y + 10
            bot_y = top_y + rw_height

            poly_piste = QPolygonF([
                QPointF(cx - rw_width_top, top_y),
                QPointF(cx + rw_width_top, top_y),
                QPointF(cx + rw_width_bot, bot_y),
                QPointF(cx - rw_width_bot, bot_y)
            ])

            # Asphalte
            painter.setBrush(QBrush(QColor(30, 41, 59)))
            painter.setPen(QPen(QColor(148, 163, 184), 2))
            painter.drawPolygon(poly_piste)

            # Ligne axiale de piste (Axe central)
            painter.setPen(QPen(QColor(241, 245, 249), 2, Qt.DashLine))
            painter.drawLine(int(cx), int(top_y), int(cx), int(bot_y))

            # Feux de seuil PAPI (Verts / Rouges)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(34, 197, 94)))  # Feux verts
            painter.drawEllipse(QPointF(cx - rw_width_top - 12, top_y), 4, 4)
            painter.drawEllipse(QPointF(cx + rw_width_top + 12, top_y), 4, 4)

        # 3. Affichage Réticule HUD Cockpit
        painter.setPen(QPen(QColor(52, 211, 153), 1.5))
        painter.drawEllipse(QPointF(cx, cy), 18, 18)
        painter.drawLine(int(cx - 30), int(cy), int(cx - 18), int(cy))
        painter.drawLine(int(cx + 18), int(cy), int(cx + 30), int(cy))
        painter.drawLine(int(cx), int(cy - 18), int(cx), int(cy - 30))

        # Télémétrie HUD
        font = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(52, 211, 153))

        painter.drawText(30, 40, f"ALT : {int(self.avion.altitude)} m")
        painter.drawText(30, 60, f"SPD : {int(self.avion.vitesse)} km/h")
        painter.drawText(w - 180, 40, f"CAP : {int(self.avion.cap):03d}°")

        statut_vol = "APPROCHE ILS" if self.avion.is_landing else "VOL EN ROUTE"
        painter.drawText(int(cx - 50), 40, statut_vol)