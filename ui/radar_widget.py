import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QWidget

from ui.trajectoire import dessiner_trajectoire, piste_la_plus_proche


class RadarWidget(QWidget):

    ZOOM_MIN = 0.45
    ZOOM_MAX = 2.5
    ZOOM_STEP = 1.15
    VITESSE_DEPLACEMENT = 40

    def __init__(self, engine, on_avion_clicked):
        super().__init__()

        self.engine = engine
        self.on_avion_clicked = on_avion_clicked

        self.setMinimumSize(600, 600)
        self.setFocusPolicy(Qt.StrongFocus)

        self.zoom = 1.0
        centre_x, centre_y = self.engine.centre()
        self.camera_x = float(centre_x)
        self.camera_y = float(centre_y)

        self._deplacement_en_cours = False
        self._position_souris_precedente = None
        self._compteur_clignotement = 0

        self.fond = QColor(4, 8, 14)
        self.grille = QColor(16, 26, 40, 120)
        self.grille_forte = QColor(28, 45, 68, 180)

        self.radar_cercle = QColor(16, 185, 129, 60)
        self.radar_repere = QColor(16, 185, 129, 140)

        self.texte = QColor(226, 232, 240)
        self.texte_secondaire = QColor(100, 116, 139)

        self.piste = QColor(24, 32, 44)
        self.piste_bord = QColor(51, 65, 85)
        self.piste_marquage = QColor(241, 245, 249)

        self.setStyleSheet("background-color: rgb(4, 8, 14);")

    def paintEvent(self, event):
        self._compteur_clignotement += 1

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), self.fond)

        painter.save()
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self.zoom, self.zoom)
        painter.translate(-self.camera_x, -self.camera_y)

        self._dessiner_grille(painter)
        self._dessiner_pistes(painter)
        self._dessiner_decor_radar(painter)
        self._dessiner_vent(painter)
        self._dessiner_trajectoires(painter)
        self._dessiner_avions(painter)

        painter.restore()

        self._dessiner_interface(painter)

    def _dessiner_grille(self, painter):
        """Grille symétrique centrée autour de (0,0)."""
        taille = 1000
        pas = 50

        painter.setPen(QPen(self.grille, 1, Qt.DotLine))
        for x in range(-taille, taille + pas, pas):
            painter.drawLine(x, -taille, x, taille)
            painter.drawLine(-taille, x, taille, x)

        painter.setPen(QPen(self.grille_forte, 1, Qt.SolidLine))
        for x in range(-taille, taille + 200, 200):
            painter.drawLine(x, -taille, x, taille)
            painter.drawLine(-taille, x, taille, x)

    def _dessiner_pistes(self, painter):
        centre = self.engine.centre()

        for piste in self.engine.aeroport.pistes:
            cx, cy = piste.centre(centre)

            painter.save()
            painter.translate(cx, cy)
            painter.rotate(piste.cap)

            longueur = piste.longueur
            largeur = piste.largeur

            painter.setPen(QPen(QColor(239, 68, 68, 60), 1, Qt.DashLine))
            painter.setBrush(QColor(15, 23, 42, 180))
            painter.drawRoundedRect(-largeur / 2 - 6, -longueur / 2 - 10, largeur + 12, longueur + 20, 4, 4)

            painter.setBrush(QBrush(self.piste))
            painter.setPen(QPen(self.piste_bord, 1.5))
            painter.drawRect(-largeur / 2, -longueur / 2, largeur, longueur)

            painter.setPen(QPen(self.piste_marquage, 1.5, Qt.DashLine))
            painter.drawLine(0, -longueur / 2 + 15, 0, longueur / 2 - 15)

            painter.setPen(QPen(self.piste_marquage, 2))
            for cote in (-longueur / 2 + 2, longueur / 2 - 2):
                d = 1 if cote < 0 else -1
                for x in range(-int(largeur / 2) + 4, int(largeur / 2) - 2, 5):
                    painter.drawLine(x, cote, x, cote + d * 12)

            painter.setPen(QPen(QColor(251, 191, 36), 2))
            painter.drawLine(-largeur / 2, -longueur / 2, largeur / 2, -longueur / 2)
            painter.drawLine(-largeur / 2, longueur / 2, largeur / 2, longueur / 2)

            self._dessiner_texte(painter, piste.nom, 0, -longueur / 2 - 14, QColor(251, 191, 36), centre=True, gras=True)

            painter.restore()

    def _dessiner_decor_radar(self, painter):
        cx, cy = self.engine.centre()

        painter.save()
        painter.translate(cx, cy)

        painter.setBrush(Qt.NoBrush)
        rayons = (100, 200, 300)

        for idx, rayon in enumerate(rayons):
            painter.setPen(QPen(self.radar_cercle, 1, Qt.DashLine))
            painter.drawEllipse(QPointF(0, 0), rayon, rayon)
            self._dessiner_texte(painter, f"{(idx + 1) * 5}NM", 5, -rayon + 12, QColor(16, 185, 129, 140))

        painter.setPen(QPen(self.radar_repere, 1))
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            painter.drawLine(QPointF(285 * math.sin(rad), -285 * math.cos(rad)), QPointF(300 * math.sin(rad), -300 * math.cos(rad)))

        directions = ((0, "N"), (90, "E"), (180, "S"), (270, "W"))
        for angle, lettre in directions:
            rad = math.radians(angle)
            self._dessiner_texte(painter, lettre, 270 * math.sin(rad), -270 * math.cos(rad) + 4, QColor(52, 211, 153), centre=True, gras=True)

        painter.restore()

    def _dessiner_vent(self, painter):
        cx, cy = self.engine.centre()
        vent = self.engine.vent
        origine = QPointF(cx + 260, cy - 260)

        painter.save()
        painter.translate(origine)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(15, 23, 42, 200))
        painter.drawEllipse(QPointF(0, 0), 22, 22)

        painter.setPen(QPen(QColor(56, 189, 248), 1.5))
        painter.drawEllipse(QPointF(0, 0), 22, 22)

        painter.rotate(vent.direction)
        painter.setPen(QPen(QColor(56, 189, 248), 2))
        painter.drawLine(0, -14, 0, 14)
        painter.drawLine(0, -14, -5, -6)
        painter.drawLine(0, -14, 5, -6)

        painter.restore()

        self._dessiner_texte(painter, f"WIND {vent.direction:03d}° / {vent.vitesse}KT", int(origine.x()), int(origine.y()) + 36, QColor(56, 189, 248), centre=True, gras=True)

    def _dessiner_trajectoires(self, painter):
        centre = self.engine.centre()
        for avion in self.engine.avions:
            if not avion.selected:
                continue
            piste = avion.piste_visee or piste_la_plus_proche(avion, self.engine.aeroport.pistes, centre)
            if piste is not None:
                dessiner_trajectoire(painter, avion, piste, centre)

    @staticmethod
    def _silhouette_avion() -> QPolygonF:
        return QPolygonF([
            QPointF(15, 0),
            QPointF(4, -1.5),
            QPointF(1, -9),
            QPointF(-1.5, -9),
            QPointF(-1.5, -1.5),
            QPointF(-9, -1.5),
            QPointF(-12, -6),
            QPointF(-13, -6),
            QPointF(-11, 0),
            QPointF(-13, 6),
            QPointF(-12, 6),
            QPointF(-9, 1.5),
            QPointF(-1.5, 1.5),
            QPointF(-1.5, 9),
            QPointF(1, 9),
            QPointF(4, 1.5),
        ])

    def _dessiner_avions(self, painter):
        clignote_visible = (self._compteur_clignotement // 6) % 2 == 0

        for avion in self.engine.avions:
            if avion.en_alerte and clignote_visible:
                painter.setPen(QPen(QColor(239, 68, 68), 1.5, Qt.DashLine))
                painter.setBrush(QColor(239, 68, 68, 40))
                painter.drawEllipse(QPointF(avion.x, avion.y), 22, 22)

            painter.save()
            painter.translate(avion.x, avion.y)
            painter.rotate(avion.cap - 90)

            if avion.en_alerte:
                couleur = QColor(248, 113, 113)
            elif avion.selected:
                couleur = QColor(56, 189, 248)
            else:
                couleur = QColor(52, 211, 153)

            painter.setBrush(QBrush(couleur))
            painter.setPen(QPen(QColor(241, 245, 249), 1))
            painter.drawPolygon(self._silhouette_avion())
            painter.restore()

            pt_avion = QPointF(avion.x, avion.y)
            pt_label = QPointF(avion.x + 18, avion.y - 18)

            painter.setPen(QPen(couleur, 1, Qt.DotLine))
            painter.drawLine(pt_avion, pt_label)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(15, 23, 42, 210))
            painter.drawRoundedRect(pt_label.x(), pt_label.y() - 12, 72, 26, 4, 4)

            painter.setPen(QPen(couleur, 1))
            painter.drawRoundedRect(pt_label.x(), pt_label.y() - 12, 72, 26, 4, 4)

            self._dessiner_texte(painter, avion.name, pt_label.x() + 4, pt_label.y() - 1, couleur, gras=True)
            self._dessiner_texte(painter, f"FL{int(avion.altitude//100):03d} {int(avion.vitesse)}KT", pt_label.x() + 4, pt_label.y() + 10, QColor(226, 232, 240))

    def _dessiner_interface(self, painter):
        painter.setPen(QPen(QColor(56, 189, 248, 80), 1))
        painter.setBrush(QColor(15, 23, 42, 220))
        painter.drawRoundedRect(14, 14, 160, 68, 8, 8)

        self._dessiner_texte(painter, f"RADAR ZOOM : {self.zoom:.2f}x", 24, 34, QColor(56, 189, 248), gras=True)
        self._dessiner_texte(painter, "MOLETTE : ZOOM IN/OUT", 24, 52, QColor(148, 163, 184))
        self._dessiner_texte(painter, "GLISSER  : PANORAMIQUE", 24, 68, QColor(148, 163, 184))

        aeroport = self.engine.aeroport
        largeur = 220

        painter.setPen(QPen(QColor(56, 189, 248, 80), 1))
        painter.setBrush(QColor(15, 23, 42, 220))
        painter.drawRoundedRect(self.width() - largeur - 14, 14, largeur, 58, 8, 8)

        self._dessiner_texte(painter, f"{aeroport.code_icao} / {aeroport.code_iata}", self.width() - largeur + 10, 36, QColor(241, 245, 249), gras=True)
        self._dessiner_texte(painter, aeroport.nom.upper(), self.width() - largeur + 10, 54, QColor(148, 163, 184))

    @staticmethod
    def _dessiner_texte(painter, texte, x, y, couleur, centre=False, gras=False):
        font = QFont("Consolas", 8)
        font.setStyleHint(QFont.Monospace)
        font.setBold(gras)
        painter.setFont(font)

        painter.setPen(QColor(4, 8, 14, 220))
        if centre:
            largeur = painter.fontMetrics().horizontalAdvance(texte)
            painter.drawText(int(x - largeur / 2 + 1), int(y + 1), texte)
            painter.setPen(couleur)
            painter.drawText(int(x - largeur / 2), int(y), texte)
        else:
            painter.drawText(int(x + 1), int(y + 1), texte)
            painter.setPen(couleur)
            painter.drawText(int(x), int(y), texte)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            avion = self._avion_sous_souris(event.position())
            if avion is not None:
                self.on_avion_clicked(avion)
                return

            self._deplacement_en_cours = True
            self._position_souris_precedente = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            self.setFocus()

    def mouseMoveEvent(self, event):
        if not self._deplacement_en_cours or self._position_souris_precedente is None:
            return

        position_actuelle = event.position()
        delta = position_actuelle - self._position_souris_precedente

        self.camera_x -= delta.x() / self.zoom
        self.camera_y -= delta.y() / self.zoom

        self._position_souris_precedente = position_actuelle
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._deplacement_en_cours = False
            self._position_souris_precedente = None
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        position_souris = event.position()
        monde_avant = self._ecran_vers_monde(position_souris)

        if event.angleDelta().y() > 0:
            nouveau_zoom = self.zoom * self.ZOOM_STEP
        else:
            nouveau_zoom = self.zoom / self.ZOOM_STEP

        nouveau_zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, nouveau_zoom))

        if nouveau_zoom == self.zoom:
            return

        self.zoom = nouveau_zoom
        monde_apres = self._ecran_vers_monde(position_souris)

        self.camera_x += monde_avant[0] - monde_apres[0]
        self.camera_y += monde_avant[1] - monde_apres[1]
        self.update()

    def keyPressEvent(self, event):
        touche = event.key()

        if touche == Qt.Key_R:
            self.recentrer()
            return

        if touche in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom = min(self.ZOOM_MAX, self.zoom * self.ZOOM_STEP)
            self.update()
            return

        if touche == Qt.Key_Minus:
            self.zoom = max(self.ZOOM_MIN, self.zoom / self.ZOOM_STEP)
            self.update()
            return

        deplacement = self.VITESSE_DEPLACEMENT / self.zoom

        if touche == Qt.Key_Left:
            self.camera_x -= deplacement
        elif touche == Qt.Key_Right:
            self.camera_x += deplacement
        elif touche == Qt.Key_Up:
            self.camera_y -= deplacement
        elif touche == Qt.Key_Down:
            self.camera_y += deplacement
        else:
            super().keyPressEvent(event)
            return

        self.update()

    def _ecran_vers_monde(self, position) -> tuple[float, float]:
        monde_x = self.camera_x + (position.x() - self.width() / 2) / self.zoom
        monde_y = self.camera_y + (position.y() - self.height() / 2) / self.zoom
        return monde_x, monde_y

    def _monde_vers_ecran(self, x, y) -> tuple[float, float]:
        ecran_x = self.width() / 2 + (x - self.camera_x) * self.zoom
        ecran_y = self.height() / 2 + (y - self.camera_y) * self.zoom
        return ecran_x, ecran_y

    def _avion_sous_souris(self, position):
        monde_x, monde_y = self._ecran_vers_monde(position)
        rayon_selection = 20 / self.zoom

        avion_selectionne = None
        distance_min = float("inf")

        for avion in self.engine.avions:
            distance = math.hypot(avion.x - monde_x, avion.y - monde_y)
            if distance <= rayon_selection and distance < distance_min:
                avion_selectionne = avion
                distance_min = distance

        return avion_selectionne

    def recentrer(self):
        centre_x, centre_y = self.engine.centre()
        self.camera_x = float(centre_x)
        self.camera_y = float(centre_y)
        self.zoom = 1.0
        self.update()