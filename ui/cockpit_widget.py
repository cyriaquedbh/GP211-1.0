import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QDialog


class CockpitWidget(QDialog):
    """Fenêtre simulant la vue cockpit avec rendu dynamique de la piste selon le cap et la position."""

    def __init__(self, avion, engine, parent=None):
        super().__init__(parent)
        self.avion = avion
        self.engine = engine

        self.setWindowTitle(f"Cockpit HUD — {avion.name}")
        self.resize(850, 520)
        self.setStyleSheet("background-color: #04080e;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # 1. Horizon artificiel & Pitch
        pitch = min(30.0, max(-30.0, (self.avion.altitude - 1000) / 100))
        horizon_y = cy + pitch * 3.0

        # Ciel & Sol
        painter.fillRect(0, 0, w, int(horizon_y), QColor(15, 23, 42))
        painter.fillRect(
            0, int(horizon_y), w, int(h - horizon_y), QColor(16, 26, 20)
        )

        # Ligne d'horizon
        painter.setPen(QPen(QColor(56, 189, 248, 160), 1.5))
        painter.drawLine(0, int(horizon_y), w, int(horizon_y))

        # 2. Rendu dynamique de la piste orientée selon le cap de l'avion
        self._dessiner_piste_orientee(painter, cx, cy, horizon_y)

        # 3. Rendu des autres avions en vol
        self._dessiner_trafic_intercepte(painter, cx, cy, horizon_y)

        # 4. Instrumentation HUD & ILS
        self._dessiner_hud_et_ils(painter, cx, cy)

        # Télémétrie texte
        font = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(52, 211, 153))

        painter.drawText(30, 40, f"ALT : {int(self.avion.altitude)} M")
        painter.drawText(30, 60, f"SPD : {int(self.avion.vitesse)} KM/H")
        painter.drawText(w - 180, 40, f"CAP : {int(self.avion.cap):03d}°")

        mode = (
            "HOLDING"
            if self.avion.is_holding
            else ("ILS LANDING" if self.avion.is_landing else "CRUISE")
        )
        painter.drawText(int(cx - 45), 40, mode)

    def _dessiner_piste_orientee(self, painter, cx, cy, horizon_y):
        """Projette les extrémités de la piste selon la position et le cap réel de l'avion."""
        piste = self.avion.piste_visee
        if piste is None:
            return

        centre_aeroport = self.engine.centre()
        px, py = piste.centre(centre_aeroport)

        # Calcul des deux extrémités de la piste (Seuil & Fond de piste)
        cap_piste_rad = math.radians(piste.cap)
        half_len = piste.longueur / 2

        # Points mondes des seuils
        p1_x, p1_y = px - math.sin(cap_piste_rad) * half_len, py + math.cos(
            cap_piste_rad
        ) * half_len
        p2_x, p2_y = px + math.sin(cap_piste_rad) * half_len, py - math.cos(
            cap_piste_rad
        ) * half_len

        # Conversion des points dans le repère de l'avion (Translation + Rotation du cap avion)
        def monde_vers_cockpit(pt_x, pt_y):
            dx = pt_x - self.avion.x
            dy = pt_y - self.avion.y

            cap_avion_rad = math.radians(self.avion.cap)

            # Transformed coordinates: X = latéral (gauche/droite), Y = profondeur (devant)
            local_x = dx * math.cos(cap_avion_rad) - dy * math.sin(
                cap_avion_rad
            )
            local_y = dx * math.sin(cap_avion_rad) + dy * math.cos(
                cap_avion_rad
            )

            return local_x, local_y

        # Transformer les 4 coins du rectangle de la piste
        hw = piste.largeur / 2
        cos_p, sin_p = math.cos(cap_piste_rad), math.sin(cap_piste_rad)

        corners_world = [
            (p1_x - cos_p * hw, p1_y - sin_p * hw),
            (p1_x + cos_p * hw, p1_y + sin_p * hw),
            (p2_x + cos_p * hw, p2_y + sin_p * hw),
            (p2_x - cos_p * hw, p2_y - sin_p * hw),
        ]

        screen_points = []
        altitude_factor = max(100.0, self.avion.altitude)

        for cw_x, cw_y in corners_world:
            lx, ly = monde_vers_cockpit(cw_x, cw_y)

            # Si le point est derrière l'avion, on le clippe devant pour éviter les inversions
            if ly <= 1.0:
                ly = 1.0

            # Perspective 3D -> 2D
            scale = 400.0 / (ly + 50.0)
            sx = cx + lx * scale
            sy = horizon_y + (altitude_factor / (ly + 10.0)) * 2.5

            screen_points.append(QPointF(sx, sy))

        # Dessin du polygone de la piste en perspective
        poly_piste = QPolygonF(screen_points)

        painter.setBrush(QBrush(QColor(30, 41, 59)))
        painter.setPen(QPen(QColor(148, 163, 184), 1.5))
        painter.drawPolygon(poly_piste)

        # Ligne médiane axiale
        m1_x, m1_y = monde_vers_cockpit(p1_x, p1_y)
        m2_x, m2_y = monde_vers_cockpit(p2_x, p2_y)

        if m1_y > 1.0 and m2_y > 1.0:
            scale1 = 400.0 / (m1_y + 50.0)
            scale2 = 400.0 / (m2_y + 50.0)

            sx1, sy1 = cx + m1_x * scale1, horizon_y + (
                altitude_factor / (m1_y + 10.0)
            ) * 2.5
            sx2, sy2 = cx + m2_x * scale2, horizon_y + (
                altitude_factor / (m2_y + 10.0)
            ) * 2.5

            painter.setPen(QPen(QColor(241, 245, 249), 1.5, Qt.DashLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def _dessiner_trafic_intercepte(self, painter, cx, cy, horizon_y):
        """Affiche les avions présents dans le champ de vision avant."""
        cap_rad = math.radians(self.avion.cap)
        dir_x, dir_y = math.sin(cap_rad), -math.cos(cap_rad)

        for autre in self.engine.avions:
            if autre is self.avion:
                continue

            dx = autre.x - self.avion.x
            dy = autre.y - self.avion.y
            dist = math.hypot(dx, dy)

            if dist > 500 or dist < 5:
                continue

            dot = (dx * dir_x + dy * dir_y) / dist
            if dot > 0.3:
                angle_autre = math.degrees(math.atan2(dx, -dy)) % 360
                diff_angle = (angle_autre - self.avion.cap + 540) % 360 - 180

                screen_x = cx + diff_angle * 10
                diff_alt = (autre.altitude - self.avion.altitude) / 40
                screen_y = horizon_y - diff_alt

                taille = max(4.0, 22.0 * (1.0 - dist / 500))

                painter.setPen(QPen(QColor(248, 113, 113), 1.5))
                painter.setBrush(QColor(239, 68, 68, 80))
                painter.drawRect(
                    int(screen_x - taille / 2),
                    int(screen_y - taille / 2),
                    int(taille),
                    int(taille),
                )

                font = QFont("Consolas", 8)
                painter.setFont(font)
                painter.drawText(
                    int(screen_x + taille),
                    int(screen_y + 4),
                    f"{autre.name} ({int(autre.altitude)}m)",
                )

    def _dessiner_hud_et_ils(self, painter, cx, cy):
        """Dessine le collimateur principal et les deux losanges ILS (Localizer & Glide Path)."""
        painter.setPen(QPen(QColor(52, 211, 153, 200), 1.5))
        painter.drawEllipse(QPointF(cx, cy), 16, 16)
        painter.drawLine(int(cx - 28), int(cy), int(cx - 16), int(cy))
        painter.drawLine(int(cx + 16), int(cy), int(cx + 28), int(cy))

        if not self.avion.is_landing or self.avion.piste_visee is None:
            return

        centre_aeroport = self.engine.centre()
        proj, ecart_lat = self.avion._position_relative_piste(centre_aeroport)

        # 1. LOCALIZER (Axe horizontal)
        dev_loc = max(-60.0, min(60.0, ecart_lat))
        loc_x = cx + (dev_loc * 1.5)

        poly_loc = QPolygonF([
            QPointF(loc_x, cy + 110),
            QPointF(loc_x + 6, cy + 116),
            QPointF(loc_x, cy + 122),
            QPointF(loc_x - 6, cy + 116),
        ])
        painter.setBrush(QBrush(QColor(251, 191, 36)))
        painter.setPen(QPen(QColor(245, 158, 11), 1))
        painter.drawPolygon(poly_loc)
        painter.drawLine(
            int(cx - 80), int(cy + 116), int(cx + 80), int(cy + 116)
        )

        # 2. GLIDE SLOPE (Plan vertical)
        dist_seuil = abs(proj)
        alt_ideale = dist_seuil * 12.0
        ecart_alt = self.avion.altitude - alt_ideale
        dev_glide = max(-60.0, min(60.0, ecart_alt / 10))
        glide_y = cy + (dev_glide * 1.5)

        poly_glide = QPolygonF([
            QPointF(cx + 116, glide_y),
            QPointF(cx + 122, glide_y + 6),
            QPointF(cx + 116, glide_y + 12),
            QPointF(cx + 110, glide_y + 6),
        ])
        painter.drawPolygon(poly_glide)
        painter.drawLine(
            int(cx + 116), int(cy - 80), int(cx + 116), int(cy + 80)
        )