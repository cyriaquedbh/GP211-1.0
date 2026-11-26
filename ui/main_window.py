from PySide6.QtCore import QDateTime, QElapsedTimer, QTimer, Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config.airports import Aeroport
from controllers.instructions import (
    Attendre,
    Atterrir,
    ChangerCap,
    Descendre,
    Instruction,
    Monter,
    Retour,
)
from controllers.simulation_engine import SimulationEngine
from models.avion import Avion
from ui import styles
from ui.cockpit_widget import CockpitWidget
from ui.radar_widget import RadarWidget


class SimulateurATC(QMainWindow):
    PAS_TIMER_MS = 50
    DT_MAX = 0.25               # s : borne le pas si l'application a été figée (fenêtre déplacée...)
    DUREE_RETOUR = 4.0          # s d'affichage du retour d'un ordre

    PAS_ALTITUDE_BOUTON = 100   # m
    PAS_ALTITUDE_CLAVIER = 50   # m
    PAS_CAP_CLAVIER = 2         # °

    def __init__(self, aeroport: Aeroport) -> None:
        super().__init__()

        self.aeroport = aeroport
        self.setWindowTitle(f"ATC Radar Command — {aeroport.nom}")
        self.setMinimumSize(1280, 760)

        self.engine = SimulationEngine(aeroport)
        self.avion_selectionne: Avion | None = None
        self.cockpit_dialog: CockpitWidget | None = None
        self._retour_restant = 0.0

        self.setStyleSheet(styles.STYLE_GLOBAL)
        self.setFocusPolicy(Qt.StrongFocus)

        self._init_ui()

        # La simulation avance au temps réel mesuré, pas à un pas supposé constant.
        self._chrono = QElapsedTimer()
        self._chrono.start()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._boucle_simulation)
        self.timer.start(self.PAS_TIMER_MS)

    # ------------------------------------------------------------------ construction UI

    def _init_ui(self) -> None:
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        titre = QLabel("AIR TRAFFIC CONTROL")
        titre.setStyleSheet(styles.STYLE_TITRE)

        sous_titre = QLabel("MONITORING SYSTEM")
        sous_titre.setStyleSheet(styles.STYLE_SOUS_TITRE)

        header_layout.addWidget(titre)
        header_layout.addWidget(sous_titre)
        left_panel.addLayout(header_layout)

        info_group = QGroupBox("TÉLÉMÉTRIE SYSTÈME")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        self.lbl_heure = QLabel("UTC : --:--:--")
        self.lbl_heure.setStyleSheet(styles.STYLE_HEURE)

        self.lbl_vent = QLabel("VENT : ---° / --- km/h")
        self.lbl_vent.setStyleSheet(styles.STYLE_VENT)

        self.lbl_stats = QLabel(f"SCORE : {self.engine.score}")
        self.lbl_stats.setStyleSheet(styles.STYLE_STATS_OK)

        info_layout.addWidget(self.lbl_heure)
        info_layout.addWidget(self.lbl_vent)
        info_layout.addWidget(self.lbl_stats)
        info_group.setLayout(info_layout)
        left_panel.addWidget(info_group)

        avions_group = QGroupBox("TRAFIC EN VOL")
        avions_layout = QVBoxLayout()
        avions_layout.setContentsMargins(6, 12, 6, 6)

        self.list_avions = QListWidget()
        self.list_avions.setMinimumWidth(320)
        self.list_avions.setMinimumHeight(420)
        self.list_avions.itemClicked.connect(self._selection_via_liste)

        avions_layout.addWidget(self.list_avions)
        avions_group.setLayout(avions_layout)
        left_panel.addWidget(avions_group, 1)

        radar_container = QFrame()
        radar_container.setStyleSheet(styles.STYLE_RADAR_CONTENEUR)
        radar_layout = QVBoxLayout(radar_container)
        radar_layout.setContentsMargins(6, 6, 6, 6)

        self.radar = RadarWidget(self.engine, self._selection_via_radar)
        radar_layout.addWidget(self.radar)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)

        controls_group = QGroupBox("ORDRES DE SÉCURITÉ")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)

        self.lbl_avion = QLabel("AUCUNE CIBLE SÉLECTIONNÉE")
        self.lbl_avion.setAlignment(Qt.AlignCenter)
        self.lbl_avion.setStyleSheet(styles.STYLE_AVION_VIDE)

        self.lbl_cap = QLabel("CAP : ---°")
        self.lbl_cap.setAlignment(Qt.AlignCenter)
        self.lbl_cap.setStyleSheet(styles.STYLE_CAP)

        self.cap_slider = QSlider(Qt.Horizontal)
        self.cap_slider.setRange(0, 359)
        self.cap_slider.setMinimumHeight(30)
        self.cap_slider.valueChanged.connect(self._cap_slider_change)

        lbl_astuce = QLabel(
            "RACCOURCIS CLAVIER (Maintien fluide)\n◄ / ► : Ajuster le cap\n▲ / ▼ : Ajuster l'altitude"
        )
        lbl_astuce.setAlignment(Qt.AlignCenter)
        lbl_astuce.setStyleSheet(styles.STYLE_ASTUCE)

        btn_up = QPushButton(f"▲   MONTER  (+{self.PAS_ALTITUDE_BOUTON}m)")
        btn_up.setObjectName("btnMonter")
        btn_up.clicked.connect(lambda: self._executer(Monter))

        btn_down = QPushButton(f"▼   DESCENDRE  (-{self.PAS_ALTITUDE_BOUTON}m)")
        btn_down.setObjectName("btnDescendre")
        btn_down.clicked.connect(lambda: self._executer(Descendre))

        btn_land = QPushButton("🛬   AUTORISER ATTERRISSAGE")
        btn_land.setObjectName("btnAtterrir")
        btn_land.clicked.connect(lambda: self._executer(Atterrir))

        btn_hold = QPushButton("🔄   ATTENTE (CIRCUIT 360°)")
        btn_hold.setObjectName("btnAttente")
        btn_hold.clicked.connect(lambda: self._executer(Attendre))

        btn_cockpit = QPushButton("👁   VUE COCKPIT")
        btn_cockpit.setObjectName("btnCockpit")
        btn_cockpit.clicked.connect(self._ouvrir_vue_cockpit)

        self.lbl_retour = QLabel("")
        self.lbl_retour.setAlignment(Qt.AlignCenter)
        self.lbl_retour.setWordWrap(True)
        self.lbl_retour.setMinimumHeight(40)
        self.lbl_retour.setStyleSheet(styles.STYLE_RETOUR_VIDE)

        controls_layout.addWidget(self.lbl_avion)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(self.lbl_cap)
        controls_layout.addWidget(self.cap_slider)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(lbl_astuce)
        controls_layout.addSpacing(8)
        controls_layout.addWidget(btn_up)
        controls_layout.addWidget(btn_down)
        controls_layout.addSpacing(6)
        controls_layout.addWidget(btn_land)
        controls_layout.addWidget(btn_hold)
        controls_layout.addWidget(btn_cockpit)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(self.lbl_retour)

        controls_group.setLayout(controls_layout)
        right_panel.addWidget(controls_group)
        right_panel.addStretch()

        main_layout.addLayout(left_panel, 2)
        main_layout.addWidget(radar_container, 5)
        main_layout.addLayout(right_panel, 2)

        self.setCentralWidget(main_widget)

    # ------------------------------------------------------------------ sélection

    def _selection_via_radar(self, avion: Avion) -> None:
        self.engine.selectionner(avion)
        self.avion_selectionne = avion
        self._synchroniser_slider(avion.target_cap)
        self._mettre_a_jour_avion_selectionne()

    def _selection_via_liste(self, item: QListWidgetItem) -> None:
        avion = item.data(Qt.UserRole)
        if avion in self.engine.avions:
            self._selection_via_radar(avion)

    def _mettre_a_jour_avion_selectionne(self) -> None:
        if not self.avion_selectionne:
            self.lbl_avion.setText("AUCUNE CIBLE SÉLECTIONNÉE")
            self.lbl_avion.setStyleSheet(styles.STYLE_AVION_VIDE)
            return

        avion = self.avion_selectionne
        statut = ""
        if avion.is_holding:
            statut = " [HOLDING]"
        elif avion.is_landing:
            statut = " [APPROCHE]"
        self.lbl_avion.setText(f"✈ {avion.name}{statut}\nALTITUDE: {int(avion.altitude)} m")
        self.lbl_avion.setStyleSheet(styles.STYLE_AVION_ACTIF)

    def _synchroniser_slider(self, valeur_cap: float) -> None:
        self.cap_slider.blockSignals(True)
        self.cap_slider.setValue(int(valeur_cap))
        self.cap_slider.blockSignals(False)
        self.lbl_cap.setText(f"CAP : {int(valeur_cap):03d}°")

    # ------------------------------------------------------------------ ordres

    def _appliquer(self, instruction: Instruction) -> Retour:
        retour = instruction.executer()
        self._afficher_retour(retour)
        return retour

    def _afficher_retour(self, retour: Retour) -> None:
        self.lbl_retour.setText(retour.message)
        self.lbl_retour.setStyleSheet(
            styles.STYLE_RETOUR_OK if retour.ok else styles.STYLE_RETOUR_ERREUR
        )
        self._retour_restant = self.DUREE_RETOUR

    def _cap_slider_change(self, valeur: int) -> None:
        self.lbl_cap.setText(f"CAP : {valeur:03d}°")
        if self.avion_selectionne:
            retour = ChangerCap(self.avion_selectionne, valeur).executer()
            # Le glissement génère de nombreux ordres : on n'affiche que les annulations.
            if retour.annulations:
                self._afficher_retour(retour)

    def _executer(self, classe_instruction: type[Instruction]) -> None:
        avion = self.avion_selectionne
        if avion is None:
            return

        if classe_instruction is Atterrir:
            piste = self.engine.piste_pour_atterrissage(avion)
            instruction = Atterrir(avion, piste, self.engine.vent, self.engine.centre())
        elif classe_instruction in (Monter, Descendre):
            instruction = classe_instruction(avion, delta=self.PAS_ALTITUDE_BOUTON)
        else:
            instruction = classe_instruction(avion)

        self._appliquer(instruction)

    def keyPressEvent(self, event) -> None:
        avion = self.avion_selectionne
        if avion is not None:
            touche = event.key()

            if touche in (Qt.Key_Left, Qt.Key_Right):
                delta = -self.PAS_CAP_CLAVIER if touche == Qt.Key_Left else self.PAS_CAP_CLAVIER
                self._appliquer(ChangerCap(avion, avion.target_cap + delta))
                self._synchroniser_slider(avion.target_cap)
                return

            if touche == Qt.Key_Up:
                self._appliquer(Monter(avion, self.PAS_ALTITUDE_CLAVIER))
                return

            if touche == Qt.Key_Down:
                self._appliquer(Descendre(avion, self.PAS_ALTITUDE_CLAVIER))
                return

        super().keyPressEvent(event)

    # ------------------------------------------------------------------ cockpit

    def _ouvrir_vue_cockpit(self) -> None:
        if self.avion_selectionne:
            self.cockpit_dialog = CockpitWidget(self.avion_selectionne, self.engine, self)
            self.cockpit_dialog.show()

    def _fermer_cockpit(self) -> None:
        if self.cockpit_dialog is not None:
            self.cockpit_dialog.close()
            self.cockpit_dialog = None

    # ------------------------------------------------------------------ rafraîchissement

    @staticmethod
    def _texte_carte(avion: Avion) -> str:
        statut = ""
        if avion.is_holding:
            statut = "  ↻ ATTENTE"
        elif avion.is_landing:
            statut = "  ▸ APPROCHE"
        if avion.carburant_faible:
            statut += "  ⛽ FUEL BAS"

        return (
            f"✈ {avion.name}{statut}\n"
            f"ALT : {int(avion.altitude)} m   |   SPD : {int(avion.vitesse)} km/h\n"
            f"CAP : {int(avion.cap):03d}°    |   FUEL : {int(avion.fuel)}%"
        )

    def _rafraichir_liste(self) -> None:
        """Met à jour les cartes en place ; ne reconstruit la liste que si le trafic a changé."""
        avions = self.engine.avions
        presents = [self.list_avions.item(i).data(Qt.UserRole) for i in range(self.list_avions.count())]

        if len(presents) != len(avions) or any(p is not a for p, a in zip(presents, avions)):
            self.list_avions.clear()
            for avion in avions:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, avion)
                item.setFont(QFont("Consolas", 9))
                self.list_avions.addItem(item)

        for index, avion in enumerate(avions):
            item = self.list_avions.item(index)

            texte = self._texte_carte(avion)
            if item.text() != texte:
                item.setText(texte)

            if avion.selected:
                item.setBackground(QColor(14, 116, 144))
                item.setForeground(QColor(255, 255, 255))
            elif avion.en_alerte:
                item.setBackground(QColor(127, 29, 29))
                item.setForeground(QColor(254, 202, 202))
            else:
                item.setBackground(QBrush())
                item.setForeground(QBrush())

    def _rafraichir_statut(self) -> None:
        engine = self.engine

        if engine.partie_terminee:
            self.lbl_stats.setText(f"⚠ {engine.raison_fin} — SCORE : {engine.score}")
            self.lbl_stats.setStyleSheet(styles.STYLE_STATS_ALERTE)
            return

        evenement = engine.evenement_recent
        if evenement:
            self.lbl_stats.setText(f"SCORE : {engine.score}  •  {evenement}")
            style = styles.STYLE_STATS_ALERTE if engine.evenement_critique else styles.STYLE_STATS_OK
        else:
            self.lbl_stats.setText(f"SCORE : {engine.score}")
            style = styles.STYLE_STATS_OK
        self.lbl_stats.setStyleSheet(style)

    def _rafraichir_retour(self, dt: float) -> None:
        if self._retour_restant <= 0:
            return
        self._retour_restant -= dt
        if self._retour_restant <= 0:
            self.lbl_retour.setText("")
            self.lbl_retour.setStyleSheet(styles.STYLE_RETOUR_VIDE)

    def _boucle_simulation(self) -> None:
        dt = min(self._chrono.restart() / 1000.0, self.DT_MAX)

        self.lbl_heure.setText("UTC : " + QDateTime.currentDateTimeUtc().toString("HH:mm:ss"))
        self.lbl_vent.setText(
            f"VENT : {self.engine.vent.direction:03d}° / {self.engine.vent.vitesse} km/h"
        )

        self.engine.maj(dt)

        if self.avion_selectionne not in self.engine.avions:
            self.avion_selectionne = None
            self._mettre_a_jour_avion_selectionne()
        else:
            self._synchroniser_slider(self.avion_selectionne.target_cap)

        if self.cockpit_dialog is not None and self.cockpit_dialog.avion not in self.engine.avions:
            self._fermer_cockpit()

        self._rafraichir_liste()
        self._rafraichir_statut()
        self._mettre_a_jour_avion_selectionne()
        self._rafraichir_retour(dt)
        self.radar.update()

        if self.cockpit_dialog and self.cockpit_dialog.isVisible():
            self.cockpit_dialog.update()

        if self.engine.partie_terminee:
            self._fin_de_partie()

    # ------------------------------------------------------------------ fin / nouvelle partie

    def _fin_de_partie(self) -> None:
        self.timer.stop()

        engine = self.engine
        minutes, secondes = divmod(int(engine.temps_ecoule), 60)

        boite = QMessageBox(self)
        boite.setIcon(QMessageBox.Warning)
        boite.setWindowTitle("Fin de partie")
        boite.setText(f"{engine.raison_fin}")
        boite.setInformativeText(
            f"Score : {engine.score}\n"
            f"Atterrissages réussis : {engine.atterrissages_reussis}\n"
            f"Appareils perdus : {engine.crashes}\n"
            f"Sorties de secteur : {engine.sorties_secteur}\n"
            f"Durée : {minutes:02d}:{secondes:02d}"
        )
        bouton_rejouer = boite.addButton("Rejouer", QMessageBox.AcceptRole)
        boite.addButton("Quitter", QMessageBox.RejectRole)
        boite.exec()

        if boite.clickedButton() is bouton_rejouer:
            self._nouvelle_partie()
        else:
            self.close()

    def _nouvelle_partie(self) -> None:
        self._fermer_cockpit()
        self.engine = SimulationEngine(self.aeroport)
        self.avion_selectionne = None
        self.radar.engine = self.engine
        self.radar.recentrer()
        self.list_avions.clear()
        self._mettre_a_jour_avion_selectionne()
        self._retour_restant = 0.0
        self.lbl_retour.setText("")
        self.lbl_retour.setStyleSheet(styles.STYLE_RETOUR_VIDE)

        self._chrono.restart()
        self.timer.start(self.PAS_TIMER_MS)
