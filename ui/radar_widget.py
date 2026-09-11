import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QPolygonF,
    QFont,
)

from ui.trajectoire import piste_la_plus_proche, dessiner_trajectoire


class RadarWidget(QWidget):
    """
    Vue principale de la carte ATC.

    La position des avions, pistes et bâtiments est exprimée
    dans le système de coordonnées du monde.

    La caméra permet de se déplacer et de zoomer sans modifier
    les coordonnées réelles de la simulation.
    """

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

        # ----------------------------------------------------
        # Caméra
        # ----------------------------------------------------

        self.zoom = 1.0

        centre_x, centre_y = self.engine.centre()

        self.camera_x = float(centre_x)
        self.camera_y = float(centre_y)

        self._deplacement_en_cours = False
        self._position_souris_precedente = None

        # ----------------------------------------------------
        # Animation
        # ----------------------------------------------------

        self._compteur_clignotement = 0

        # ----------------------------------------------------
        # Palette
        # ----------------------------------------------------

        self.fond = QColor(8, 13, 18)

        self.grille = QColor(18, 27, 34)
        self.grille_forte = QColor(25, 38, 47)

        self.radar_cercle = QColor(35, 75, 58)

        self.texte = QColor(190, 210, 220)
        self.texte_secondaire = QColor(100, 130, 140)

        self.piste = QColor(52, 56, 60)
        self.piste_bord = QColor(125, 130, 132)

        self.taxiway = QColor(85, 76, 48)

        self.terminal = QColor(52, 67, 78)
        self.terminal_bord = QColor(95, 120, 135)

        self.cargo = QColor(58, 50, 45)
        self.maintenance = QColor(48, 55, 62)

        self.setStyleSheet(
            "background-color: rgb(8, 13, 18);"
        )

    # ========================================================
    # PEINTURE PRINCIPALE
    # ========================================================

    def paintEvent(self, event):
        self._compteur_clignotement += 1

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing,
            True
        )

        # Fond
        painter.fillRect(
            self.rect(),
            self.fond
        )

        # ----------------------------------------------------
        # Transformation monde -> écran
        # ----------------------------------------------------

        painter.save()

        painter.translate(
            self.width() / 2,
            self.height() / 2
        )

        painter.scale(
            self.zoom,
            self.zoom
        )

        painter.translate(
            -self.camera_x,
            -self.camera_y
        )

        # ----------------------------------------------------
        # Carte
        # ----------------------------------------------------

        self._dessiner_grille(painter)
        self._dessiner_zones(painter)
        self._dessiner_routes(painter)
        self._dessiner_terminaux(painter)
        self._dessiner_pistes(painter)
        self._dessiner_decor_radar(painter)
        self._dessiner_vent(painter)
        self._dessiner_trajectoires(painter)
        self._dessiner_avions(painter)

        painter.restore()

        # ----------------------------------------------------
        # Interface par-dessus la carte
        # ----------------------------------------------------

        self._dessiner_interface(painter)

    # ========================================================
    # GRILLE
    # ========================================================

    def _dessiner_grille(self, painter):
        """Dessine une grille discrète sur toute la carte."""

        taille = 1200
        pas = 50

        painter.setPen(
            QPen(
                self.grille,
                1
            )
        )

        for x in range(0, taille + pas, pas):
            painter.drawLine(
                x,
                0,
                x,
                taille
            )

        for y in range(0, taille + pas, pas):
            painter.drawLine(
                0,
                y,
                taille,
                y
            )

        # Lignes principales
        painter.setPen(
            QPen(
                self.grille_forte,
                1
            )
        )

        for x in range(0, taille + 100, 100):
            painter.drawLine(
                x,
                0,
                x,
                taille
            )

        for y in range(0, taille + 100, 100):
            painter.drawLine(
                0,
                y,
                taille,
                y
            )

    # ========================================================
    # ZONES
    # ========================================================

    def _dessiner_zones(self, painter):
        """Dessine les zones cargo, maintenance, etc."""

        aeroport = self.engine.aeroport

        if not hasattr(aeroport, "zones"):
            return

        for zone in aeroport.zones:

            if zone.type_zone == "cargo":
                couleur = self.cargo
            elif zone.type_zone == "maintenance":
                couleur = self.maintenance
            else:
                couleur = QColor(45, 50, 55)

            painter.setBrush(
                QBrush(couleur)
            )

            painter.setPen(
                QPen(
                    QColor(80, 90, 100),
                    1
                )
            )

            painter.drawRect(
                zone.x - zone.largeur / 2,
                zone.y - zone.hauteur / 2,
                zone.largeur,
                zone.hauteur
            )

            self._dessiner_texte(
                painter,
                zone.nom,
                zone.x,
                zone.y,
                QColor(115, 125, 135)
            )

    # ========================================================
    # ROUTES / TAXIWAYS
    # ========================================================

    def _dessiner_routes(self, painter):
        """Dessine les principales voies de circulation."""

        aeroport = self.engine.aeroport

        if not hasattr(aeroport, "routes"):
            return

        for route in aeroport.routes:

            if len(route.points) < 2:
                continue

            points = [
                QPointF(x, y)
                for x, y in route.points
            ]

            # Route sombre
            painter.setPen(
                QPen(
                    QColor(25, 28, 30),
                    route.largeur + 4,
                    Qt.SolidLine,
                    Qt.RoundCap,
                    Qt.RoundJoin
                )
            )

            for index in range(len(points) - 1):
                painter.drawLine(
                    points[index],
                    points[index + 1]
                )

            # Ligne centrale
            painter.setPen(
                QPen(
                    self.taxiway,
                    route.largeur,
                    Qt.SolidLine,
                    Qt.RoundCap,
                    Qt.RoundJoin
                )
            )

            for index in range(len(points) - 1):
                painter.drawLine(
                    points[index],
                    points[index + 1]
                )

    # ========================================================
    # TERMINAUX
    # ========================================================

    def _dessiner_terminaux(self, painter):
        """
        Dessine les terminaux avec un style de plan d'aéroport.

        La géométrie dépend des positions définies dans Aeroport.
        """

        aeroport = self.engine.aeroport

        if not hasattr(aeroport, "terminaux"):
            return

        for terminal in aeroport.terminaux:

            painter.save()

            painter.translate(
                terminal.x,
                terminal.y
            )

            painter.rotate(
                terminal.rotation
            )

            # Ombre
            painter.setPen(Qt.NoPen)

            painter.setBrush(
                QColor(0, 0, 0, 80)
            )

            painter.drawRoundedRect(
                -terminal.largeur / 2 + 4,
                -terminal.hauteur / 2 + 4,
                terminal.largeur,
                terminal.hauteur,
                5,
                5
            )

            # Bâtiment
            painter.setBrush(
                QBrush(self.terminal)
            )

            painter.setPen(
                QPen(
                    self.terminal_bord,
                    1.5
                )
            )

            painter.drawRoundedRect(
                -terminal.largeur / 2,
                -terminal.hauteur / 2,
                terminal.largeur,
                terminal.hauteur,
                5,
                5
            )

            # Structure intérieure
            painter.setPen(
                QPen(
                    QColor(80, 100, 112),
                    1
                )
            )

            if terminal.largeur > 70:

                x1 = -terminal.largeur / 2 + 15
                x2 = terminal.largeur / 2 - 15

                painter.drawLine(
                    x1,
                    0,
                    x2,
                    0
                )

            # Nom
            self._dessiner_texte(
                painter,
                terminal.nom,
                0,
                4,
                QColor(215, 230, 238),
                centre=True
            )

            painter.restore()

    # ========================================================
    # PISTES
    # ========================================================

    def _dessiner_pistes(self, painter):
        """Dessine les pistes avec marquages réalistes."""

        centre = self.engine.centre()

        for piste in self.engine.aeroport.pistes:

            cx, cy = piste.centre(centre)

            painter.save()

            painter.translate(
                cx,
                cy
            )

            painter.rotate(
                piste.cap
            )

            longueur = piste.longueur
            largeur = piste.largeur

            # ------------------------------------------------
            # Zone autour de la piste
            # ------------------------------------------------

            painter.setPen(Qt.NoPen)

            painter.setBrush(
                QColor(25, 28, 30)
            )

            painter.drawRoundedRect(
                -largeur / 2 - 4,
                -longueur / 2 - 4,
                largeur + 8,
                longueur + 8,
                3,
                3
            )

            # ------------------------------------------------
            # Asphalte
            # ------------------------------------------------

            painter.setBrush(
                QBrush(self.piste)
            )

            painter.setPen(
                QPen(
                    self.piste_bord,
                    1
                )
            )

            painter.drawRect(
                -largeur / 2,
                -longueur / 2,
                largeur,
                longueur
            )

            # ------------------------------------------------
            # Ligne centrale
            # ------------------------------------------------

            painter.setPen(
                QPen(
                    QColor(235, 235, 220),
                    1.5,
                    Qt.DashLine
                )
            )

            painter.drawLine(
                0,
                -longueur / 2 + 12,
                0,
                longueur / 2 - 12
            )

            # ------------------------------------------------
            # Seuils
            # ------------------------------------------------

            painter.setPen(
                QPen(
                    QColor(240, 240, 235),
                    2
                )
            )

            for cote in (
                -longueur / 2,
                longueur / 2
            ):

                direction = (
                    1
                    if cote < 0
                    else -1
                )

                for x in range(
                    -13,
                    14,
                    6
                ):

                    painter.drawLine(
                        x,
                        cote,
                        x,
                        cote + direction * 10
                    )

            # ------------------------------------------------
            # Marques latérales
            # ------------------------------------------------

            painter.setPen(
                QPen(
                    QColor(215, 215, 210),
                    2
                )
            )

            painter.drawLine(
                -largeur / 2 + 4,
                -longueur / 2 + 5,
                -largeur / 2 + 4,
                longueur / 2 - 5
            )

            painter.drawLine(
                largeur / 2 - 4,
                -longueur / 2 + 5,
                largeur / 2 - 4,
                longueur / 2 - 5
            )

            # ------------------------------------------------
            # Nom
            # ------------------------------------------------

            self._dessiner_texte(
                painter,
                piste.nom,
                0,
                -longueur / 2 - 10,
                QColor(245, 220, 90),
                centre=True
            )

            painter.restore()

    # ========================================================
    # RADAR
    # ========================================================

    def _dessiner_decor_radar(self, painter):
        """Dessine les cercles radar autour de l'aéroport."""

        cx, cy = self.engine.centre()

        painter.save()

        painter.translate(
            cx,
            cy
        )

        # Cercles
        painter.setBrush(Qt.NoBrush)

        for rayon in (
            100,
            200,
            300,
        ):

            painter.setPen(
                QPen(
                    self.radar_cercle,
                    1,
                    Qt.DotLine
                )
            )

            painter.drawEllipse(
                QPointF(0, 0),
                rayon,
                rayon
            )

        # Directions
        painter.setPen(
            QPen(
                QColor(40, 100, 75),
                1
            )
        )

        for angle in range(
            0,
            360,
            30
        ):

            rad = math.radians(angle)

            x1 = (
                285
                * math.sin(rad)
            )

            y1 = (
                -285
                * math.cos(rad)
            )

            x2 = (
                300
                * math.sin(rad)
            )

            y2 = (
                -300
                * math.cos(rad)
            )

            painter.drawLine(
                QPointF(x1, y1),
                QPointF(x2, y2)
            )

        # Points cardinaux
        font = painter.font()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)

        painter.setPen(
            QColor(75, 155, 110)
        )

        directions = (
            (0, "N"),
            (90, "E"),
            (180, "S"),
            (270, "O"),
        )

        for angle, lettre in directions:

            rad = math.radians(angle)

            x = (
                270
                * math.sin(rad)
            )

            y = (
                -270
                * math.cos(rad)
            )

            painter.drawText(
                QPointF(
                    x - 5,
                    y + 5
                ),
                lettre
            )

        painter.restore()

    # ========================================================
    # VENT
    # ========================================================

    def _dessiner_vent(self, painter):
        """Affiche la direction et la vitesse du vent."""

        cx, cy = self.engine.centre()
        vent = self.engine.vent

        origine = QPointF(
            cx + 250,
            cy - 250
        )

        painter.save()

        painter.translate(
            origine
        )

        painter.rotate(
            vent.direction
        )

        painter.setPen(
            QPen(
                QColor(70, 190, 220),
                2
            )
        )

        painter.drawLine(
            0,
            -18,
            0,
            18
        )

        painter.drawLine(
            0,
            -18,
            -5,
            -9
        )

        painter.drawLine(
            0,
            -18,
            5,
            -9
        )

        painter.restore()

        self._dessiner_texte(
            painter,
            f"VENT {vent.direction:03d}° / "
            f"{vent.vitesse} km/h",
            int(origine.x()),
            int(origine.y()) + 35,
            QColor(80, 200, 225),
            centre=True
        )

    # ========================================================
    # TRAJECTOIRES
    # ========================================================

    def _dessiner_trajectoires(self, painter):
        """Dessine la trajectoire de l'avion sélectionné."""

        centre = self.engine.centre()

        for avion in self.engine.avions:

            if not avion.selected:
                continue

            piste = (
                avion.piste_visee
                or piste_la_plus_proche(
                    avion,
                    self.engine.aeroport.pistes,
                    centre
                )
            )

            if piste is not None:
                dessiner_trajectoire(
                    painter,
                    avion,
                    piste,
                    centre
                )

    # ========================================================
    # AVIONS
    # ========================================================

    @staticmethod
    def _silhouette_avion() -> QPolygonF:
        """
        Silhouette vue du dessus.

        Le nez pointe vers la droite.
        """

        return QPolygonF([
            QPointF(13, 0),
            QPointF(5, -2),
            QPointF(2, -9),
            QPointF(0, -4),
            QPointF(-5, -3),
            QPointF(-11, -6),
            QPointF(-9, 0),
            QPointF(-11, 6),
            QPointF(-5, 3),
            QPointF(0, 4),
            QPointF(2, 9),
            QPointF(5, 2),
        ])

    def _dessiner_avions(self, painter):
        """Dessine tous les avions présents dans la simulation."""

        clignote_visible = (
            self._compteur_clignotement // 5
        ) % 2 == 0

        for avion in self.engine.avions:

            # ------------------------------------------------
            # Alerte
            # ------------------------------------------------

            if avion.en_alerte and clignote_visible:

                painter.setPen(Qt.NoPen)

                painter.setBrush(
                    QColor(255, 50, 50, 55)
                )

                painter.drawEllipse(
                    QPointF(
                        avion.x,
                        avion.y
                    ),
                    20,
                    20
                )

            # ------------------------------------------------
            # Avion
            # ------------------------------------------------

            painter.save()

            painter.translate(
                avion.x,
                avion.y
            )

            painter.rotate(
                avion.cap - 90
            )

            if avion.en_alerte:
                couleur = QColor(
                    255,
                    65,
                    65
                )

            elif avion.selected:
                couleur = QColor(
                    255,
                    175,
                    50
                )

            else:
                couleur = QColor(
                    70,
                    215,
                    225
                )

            painter.setBrush(
                QBrush(couleur)
            )

            painter.setPen(
                QPen(
                    QColor(235, 245, 250),
                    1
                )
            )

            painter.drawPolygon(
                self._silhouette_avion()
            )

            painter.restore()

            # ------------------------------------------------
            # Informations
            # ------------------------------------------------

            couleur_texte = (
                QColor(255, 210, 210)
                if avion.en_alerte
                else QColor(220, 235, 240)
            )

            self._dessiner_texte(
                painter,
                f"{avion.name}  "
                f"{int(avion.altitude)}m",
                int(avion.x) + 12,
                int(avion.y) - 10,
                couleur_texte
            )

    # ========================================================
    # INTERFACE
    # ========================================================

    def _dessiner_interface(self, painter):
        """Dessine les informations fixes par-dessus la carte."""

        # ----------------------------------------------------
        # Indicateur de zoom
        # ----------------------------------------------------

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(10, 17, 23, 220)
        )

        painter.drawRoundedRect(
            12,
            12,
            145,
            62,
            8,
            8
        )

        painter.setPen(
            QColor(180, 200, 210)
        )

        font = painter.font()
        font.setPixelSize(11)
        painter.setFont(font)

        painter.drawText(
            24,
            35,
            f"ZOOM  {self.zoom:.2f}x"
        )

        painter.setPen(
            QColor(100, 125, 135)
        )

        painter.drawText(
            24,
            56,
            "Molette : zoom"
        )

        # ----------------------------------------------------
        # Position caméra
        # ----------------------------------------------------

        painter.drawText(
            24,
            70,
            "Glisser : déplacer"
        )

        # ----------------------------------------------------
        # Nom de l'aéroport
        # ----------------------------------------------------

        aeroport = self.engine.aeroport

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(10, 17, 23, 220)
        )

        largeur = 230

        painter.drawRoundedRect(
            self.width() - largeur - 12,
            12,
            largeur,
            58,
            8,
            8
        )

        painter.setPen(
            QColor(220, 235, 240)
        )

        font = painter.font()
        font.setPixelSize(13)
        font.setBold(True)
        painter.setFont(font)

        painter.drawText(
            self.width() - largeur,
            36,
            f"{aeroport.code_icao}  •  "
            f"{aeroport.code_iata}"
        )

        font.setPixelSize(10)
        font.setBold(False)
        painter.setFont(font)

        painter.setPen(
            QColor(120, 145, 155)
        )

        painter.drawText(
            self.width() - largeur,
            56,
            aeroport.nom
        )

    # ========================================================
    # TEXTE
    # ========================================================

    @staticmethod
    def _dessiner_texte(
        painter,
        texte,
        x,
        y,
        couleur,
        centre=False
    ):
        """Dessine un texte avec une petite ombre."""

        font = painter.font()
        font.setPixelSize(10)
        font.setBold(False)

        painter.setFont(font)

        # Ombre
        painter.setPen(
            QColor(0, 0, 0, 180)
        )

        if centre:
            largeur = painter.fontMetrics().horizontalAdvance(
                texte
            )

            painter.drawText(
                int(x - largeur / 2 + 1),
                int(y + 1),
                texte
            )

        else:
            painter.drawText(
                int(x + 1),
                int(y + 1),
                texte
            )

        # Texte
        painter.setPen(
            couleur
        )

        if centre:
            largeur = painter.fontMetrics().horizontalAdvance(
                texte
            )

            painter.drawText(
                int(x - largeur / 2),
                int(y),
                texte
            )

        else:
            painter.drawText(
                int(x),
                int(y),
                texte
            )

    # ========================================================
    # SOURIS
    # ========================================================

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            # On cherche d'abord un avion.
            avion = self._avion_sous_souris(
                event.position()
            )

            if avion is not None:

                self.on_avion_clicked(
                    avion
                )

                return

            # Sinon on commence à déplacer la carte.
            self._deplacement_en_cours = True

            self._position_souris_precedente = (
                event.position()
            )

            self.setCursor(
                Qt.ClosedHandCursor
            )

            self.setFocus()

    def mouseMoveEvent(self, event):

        if not self._deplacement_en_cours:
            return

        if self._position_souris_precedente is None:
            return

        position_actuelle = event.position()

        delta = (
            position_actuelle
            - self._position_souris_precedente
        )

        # Conversion du déplacement écran
        # en déplacement dans le monde.
        self.camera_x -= (
            delta.x() / self.zoom
        )

        self.camera_y -= (
            delta.y() / self.zoom
        )

        self._position_souris_precedente = (
            position_actuelle
        )

        self.update()

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:

            self._deplacement_en_cours = False
            self._position_souris_precedente = None

            self.setCursor(
                Qt.ArrowCursor
            )

    # ========================================================
    # ZOOM
    # ========================================================

    def wheelEvent(self, event):

        position_souris = event.position()

        # Coordonnée monde sous la souris
        monde_avant = self._ecran_vers_monde(
            position_souris
        )

        if event.angleDelta().y() > 0:
            nouveau_zoom = (
                self.zoom
                * self.ZOOM_STEP
            )
        else:
            nouveau_zoom = (
                self.zoom
                / self.ZOOM_STEP
            )

        nouveau_zoom = max(
            self.ZOOM_MIN,
            min(
                self.ZOOM_MAX,
                nouveau_zoom
            )
        )

        if nouveau_zoom == self.zoom:
            return

        self.zoom = nouveau_zoom

        # Coordonnée monde sous la souris après zoom
        monde_apres = self._ecran_vers_monde(
            position_souris
        )

        # On déplace la caméra pour que le point
        # sous la souris reste au même endroit.
        self.camera_x += (
            monde_avant[0]
            - monde_apres[0]
        )

        self.camera_y += (
            monde_avant[1]
            - monde_apres[1]
        )

        self.update()

    # ========================================================
    # CLAVIER
    # ========================================================

    def keyPressEvent(self, event):

        touche = event.key()

        # Recentrage
        if touche == Qt.Key_R:

            self.recentrer()
            return

        # Zoom +
        if touche in (
            Qt.Key_Plus,
            Qt.Key_Equal
        ):

            self.zoom = min(
                self.ZOOM_MAX,
                self.zoom * self.ZOOM_STEP
            )

            self.update()
            return

        # Zoom -
        if touche == Qt.Key_Minus:

            self.zoom = max(
                self.ZOOM_MIN,
                self.zoom / self.ZOOM_STEP
            )

            self.update()
            return

        # Déplacement clavier
        deplacement = (
            self.VITESSE_DEPLACEMENT
            / self.zoom
        )

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

    # ========================================================
    # CONVERSION DES COORDONNÉES
    # ========================================================

    def _ecran_vers_monde(
        self,
        position
    ) -> tuple[float, float]:
        """Convertit une position écran en position monde."""

        monde_x = (
            self.camera_x
            + (
                position.x()
                - self.width() / 2
            ) / self.zoom
        )

        monde_y = (
            self.camera_y
            + (
                position.y()
                - self.height() / 2
            ) / self.zoom
        )

        return monde_x, monde_y

    def _monde_vers_ecran(
        self,
        x,
        y
    ) -> tuple[float, float]:
        """Convertit une position monde en position écran."""

        ecran_x = (
            self.width() / 2
            + (x - self.camera_x)
            * self.zoom
        )

        ecran_y = (
            self.height() / 2
            + (y - self.camera_y)
            * self.zoom
        )

        return ecran_x, ecran_y

    # ========================================================
    # SÉLECTION D'AVION
    # ========================================================

    def _avion_sous_souris(self, position):
        """Retourne l'avion situé sous la souris."""

        monde_x, monde_y = (
            self._ecran_vers_monde(position)
        )

        rayon_selection = (
            16 / self.zoom
        )

        avion_selectionne = None
        distance_min = float("inf")

        for avion in self.engine.avions:

            distance = math.hypot(
                avion.x - monde_x,
                avion.y - monde_y
            )

            if (
                distance <= rayon_selection
                and distance < distance_min
            ):
                avion_selectionne = avion
                distance_min = distance

        return avion_selectionne

    # ========================================================
    # RECENTRAGE
    # ========================================================

    def recentrer(self):
        """Replace la caméra au centre de l'aéroport."""

        centre_x, centre_y = (
            self.engine.centre()
        )

        self.camera_x = float(
            centre_x
        )

        self.camera_y = float(
            centre_y
        )

        self.zoom = 1.0

        self.update()