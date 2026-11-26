import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QDialog

from config.unites import ECHELLE_METRES_PAR_UNITE
from models.avion import Avion

Point3D = tuple[float, float, float]  # (droite, haut, profondeur) dans le repère caméra, en mètres


class _Camera:
    """Caméra de cockpit : position, cap et assiette (pente de vol) de l'avion.

    Projection perspective réelle : l'horizon et la piste tiennent compte de l'assiette.
    """

    PLAN_PROCHE = 5.0  # m
    ASSIETTE_MAX = math.radians(12)

    def __init__(self, avion: Avion, centre_x: float, centre_y: float, focale: float) -> None:
        self.x = avion.x * ECHELLE_METRES_PAR_UNITE
        self.y = avion.y * ECHELLE_METRES_PAR_UNITE
        self.z = avion.altitude
        self.cap = math.radians(avion.cap)
        vitesse_horizontale = max(avion.vitesse / 3.6, 1.0)
        assiette = math.atan2(avion.vitesse_verticale, vitesse_horizontale)
        # Bornée pour que l'horizon reste visible malgré la pente d'approche « jeu » assez raide.
        self.assiette = max(-self.ASSIETTE_MAX, min(self.ASSIETTE_MAX, assiette))
        self.cx, self.cy, self.focale = centre_x, centre_y, focale

    def coord(self, x_unites: float, y_unites: float, altitude: float) -> Point3D:
        """Point du monde (unités radar, altitude en m) vers le repère caméra."""
        dx = x_unites * ECHELLE_METRES_PAR_UNITE - self.x
        dy = y_unites * ECHELLE_METRES_PAR_UNITE - self.y
        dz = altitude - self.z

        avant = dx * math.sin(self.cap) - dy * math.cos(self.cap)
        droite = dx * math.cos(self.cap) + dy * math.sin(self.cap)

        cos_a, sin_a = math.cos(self.assiette), math.sin(self.assiette)
        profondeur = avant * cos_a + dz * sin_a
        haut = -avant * sin_a + dz * cos_a
        return droite, haut, profondeur

    def ecran(self, point: Point3D) -> QPointF:
        droite, haut, profondeur = point
        return QPointF(
            self.cx + self.focale * droite / profondeur,
            self.cy - self.focale * haut / profondeur,
        )

    def horizon_y(self) -> float:
        return self.cy + self.focale * math.tan(self.assiette)

    def couper_polygone(self, points: list[Point3D]) -> list[Point3D]:
        """Découpe le polygone contre le plan proche (évite les inversions derrière l'avion)."""
        sortie: list[Point3D] = []
        for i, a in enumerate(points):
            b = points[(i + 1) % len(points)]
            a_devant = a[2] >= self.PLAN_PROCHE
            b_devant = b[2] >= self.PLAN_PROCHE
            if a_devant:
                sortie.append(a)
            if a_devant != b_devant:
                t = (self.PLAN_PROCHE - a[2]) / (b[2] - a[2])
                sortie.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
        return sortie

    def couper_segment(self, a: Point3D, b: Point3D) -> tuple[Point3D, Point3D] | None:
        a_devant = a[2] >= self.PLAN_PROCHE
        b_devant = b[2] >= self.PLAN_PROCHE
        if not a_devant and not b_devant:
            return None
        if a_devant and b_devant:
            return a, b
        t = (self.PLAN_PROCHE - a[2]) / (b[2] - a[2])
        coupe = tuple(a[k] + t * (b[k] - a[k]) for k in range(3))
        return (a, coupe) if a_devant else (coupe, b)


class CockpitWidget(QDialog):
    """Fenêtre simulant la vue cockpit avec rendu de la piste selon le cap, la position et l'assiette."""

    OUVERTURE = 0.8            # focale = largeur de fenêtre * OUVERTURE
    PORTEE_TRAFIC = 20000.0    # m
    ENVERGURE = 60.0           # m, pour la taille apparente des autres avions

    def __init__(self, avion: Avion, engine, parent=None) -> None:
        super().__init__(parent)
        self.avion = avion
        self.engine = engine

        self.setWindowTitle(f"Cockpit HUD — {avion.name}")
        self.resize(850, 520)
        self.setStyleSheet("background-color: #04080e;")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        camera = _Camera(self.avion, cx, cy, w * self.OUVERTURE)

        # 1. Horizon artificiel (assiette réelle de l'avion)
        horizon_y = camera.horizon_y()
        limite = int(max(0, min(h, horizon_y)))
        painter.fillRect(0, 0, w, limite, QColor(15, 23, 42))
        painter.fillRect(0, limite, w, h - limite, QColor(16, 26, 20))

        painter.setPen(QPen(QColor(56, 189, 248, 160), 1.5))
        painter.drawLine(QPointF(0, horizon_y), QPointF(w, horizon_y))

        # 2. Piste, 3. trafic, 4. HUD
        self._dessiner_piste(painter, camera)
        self._dessiner_trafic(painter, camera, w, h)
        self._dessiner_hud_et_ils(painter, cx, cy)

        # Télémétrie texte
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
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

    def _dessiner_piste(self, painter: QPainter, camera: _Camera) -> None:
        """Projette la piste visée (polygone + ligne médiane) en perspective."""
        piste = self.avion.piste_visee
        if piste is None:
            return

        centre_x, centre_y = piste.centre(self.engine.centre())
        dir_x, dir_y = piste.direction()
        lat_x, lat_y = -dir_y, dir_x
        demi_longueur = piste.longueur / 2
        demi_largeur = piste.largeur / 2

        seuil_a = (centre_x - dir_x * demi_longueur, centre_y - dir_y * demi_longueur)
        seuil_b = (centre_x + dir_x * demi_longueur, centre_y + dir_y * demi_longueur)

        coins = [
            (seuil_a[0] - lat_x * demi_largeur, seuil_a[1] - lat_y * demi_largeur),
            (seuil_a[0] + lat_x * demi_largeur, seuil_a[1] + lat_y * demi_largeur),
            (seuil_b[0] + lat_x * demi_largeur, seuil_b[1] + lat_y * demi_largeur),
            (seuil_b[0] - lat_x * demi_largeur, seuil_b[1] - lat_y * demi_largeur),
        ]
        polygone = camera.couper_polygone([camera.coord(x, y, 0.0) for x, y in coins])

        if len(polygone) >= 3:
            painter.setBrush(QBrush(QColor(30, 41, 59)))
            painter.setPen(QPen(QColor(148, 163, 184), 1.5))
            painter.drawPolygon(QPolygonF([camera.ecran(p) for p in polygone]))

        segment = camera.couper_segment(
            camera.coord(seuil_a[0], seuil_a[1], 0.0),
            camera.coord(seuil_b[0], seuil_b[1], 0.0),
        )
        if segment is not None:
            painter.setPen(QPen(QColor(241, 245, 249), 1.5, Qt.DashLine))
            painter.drawLine(camera.ecran(segment[0]), camera.ecran(segment[1]))

    def _dessiner_trafic(self, painter: QPainter, camera: _Camera, w: int, h: int) -> None:
        """Affiche les avions situés dans le champ de vision avant."""
        painter.setFont(QFont("Consolas", 8))

        for autre in self.engine.avions:
            if autre is self.avion:
                continue

            point = camera.coord(autre.x, autre.y, autre.altitude)
            profondeur = point[2]
            if profondeur < camera.PLAN_PROCHE or profondeur > self.PORTEE_TRAFIC:
                continue

            ecran = camera.ecran(point)
            if not (-50 <= ecran.x() <= w + 50 and -50 <= ecran.y() <= h + 50):
                continue

            taille = max(4.0, min(40.0, camera.focale * self.ENVERGURE / profondeur))

            painter.setPen(QPen(QColor(248, 113, 113), 1.5))
            painter.setBrush(QColor(239, 68, 68, 80))
            painter.drawRect(
                int(ecran.x() - taille / 2),
                int(ecran.y() - taille / 2),
                int(taille),
                int(taille),
            )
            painter.drawText(
                int(ecran.x() + taille),
                int(ecran.y() + 4),
                f"{autre.name} ({int(autre.altitude)}m)",
            )

    def _dessiner_hud_et_ils(self, painter: QPainter, cx: float, cy: float) -> None:
        """Dessine le collimateur principal et les deux losanges ILS (Localizer & Glide Path)."""
        painter.setPen(QPen(QColor(52, 211, 153, 200), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), 16, 16)
        painter.drawLine(int(cx - 28), int(cy), int(cx - 16), int(cy))
        painter.drawLine(int(cx + 16), int(cy), int(cx + 28), int(cy))

        if not self.avion.is_landing or self.avion.piste_visee is None:
            return

        centre_aeroport = self.engine.centre()
        _, ecart_lat = self.avion.position_relative_piste(centre_aeroport)

        # 1. LOCALIZER (axe horizontal)
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
        painter.drawLine(int(cx - 80), int(cy + 116), int(cx + 80), int(cy + 116))

        # 2. GLIDE SLOPE (plan vertical) : même pente que celle suivie par l'avion
        ecart_alt = self.avion.altitude - self.avion.altitude_ideale(centre_aeroport)
        dev_glide = max(-60.0, min(60.0, ecart_alt / 10))
        glide_y = cy + (dev_glide * 1.5)

        poly_glide = QPolygonF([
            QPointF(cx + 116, glide_y),
            QPointF(cx + 122, glide_y + 6),
            QPointF(cx + 116, glide_y + 12),
            QPointF(cx + 110, glide_y + 6),
        ])
        painter.drawPolygon(poly_glide)
        painter.drawLine(int(cx + 116), int(cy - 80), int(cx + 116), int(cy + 80))
