from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QSlider, QGroupBox,
    QFrame
)
from PySide6.QtCore import QTimer, Qt, QTime
from PySide6.QtGui import QColor, QFont

from controllers.simulation_engine import SimulationEngine
from controllers.instructions import ChangerCap, Monter, Descendre, Atterrir
from ui.radar_widget import RadarWidget


# ============================================================
# STYLE GLOBAL
# ============================================================

STYLE_GLOBAL = """
QMainWindow {
    background-color: #10141b;
}

QWidget {
    color: #e8edf2;
    font-family: "Segoe UI", Arial, sans-serif;
}

QGroupBox {
    background-color: #171d26;
    border: 1px solid #2b3440;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-size: 13px;
    font-weight: bold;
    color: #9fb3c8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #8fa8bf;
}

QLabel {
    color: #dce4ec;
}

QListWidget {
    background-color: #141a22;
    border: 1px solid #2b3440;
    border-radius: 7px;
    outline: none;
    padding: 4px;
    font-size: 13px;
}

QListWidget::item {
    background-color: transparent;
    border-radius: 5px;
    padding: 9px 8px;
    margin: 2px 0;
}

QListWidget::item:hover {
    background-color: #202a36;
}

QListWidget::item:selected {
    background-color: #263b52;
    color: white;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #2c3541;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #4a9eff;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #e8f1fa;
    border: 2px solid #4a9eff;
    border-radius: 8px;
}

QPushButton {
    background-color: #202a35;
    border: 1px solid #354454;
    border-radius: 6px;
    color: #e8edf2;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 10px;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #2b3948;
    border-color: #4a9eff;
}

QPushButton:pressed {
    background-color: #17202a;
}

QPushButton#btnMonter:hover {
    border-color: #48c78e;
}

QPushButton#btnDescendre:hover {
    border-color: #f0ad4e;
}

QPushButton#btnAtterrir {
    background-color: #26372f;
    border-color: #3d7058;
}

QPushButton#btnAtterrir:hover {
    background-color: #304b3d;
    border-color: #5bc98b;
}

QFrame#separator {
    background-color: #2b3440;
}
"""


class SimulateurATC(QMainWindow):

    def __init__(self, aeroport):
        super().__init__()

        self.setWindowTitle(f"Simulateur ATC — {aeroport.nom}")
        self.setMinimumSize(1200, 720)

        self.engine = SimulationEngine(aeroport)
        self.avion_selectionne = None

        self.setStyleSheet(STYLE_GLOBAL)
        self.setFocusPolicy(Qt.StrongFocus)

        self._init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self._boucle_simulation)
        self.timer.start(50)

    # ========================================================
    # INTERFACE
    # ========================================================

    def _init_ui(self):

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        # ----------------------------------------------------
        # PANNEAU GAUCHE
        # ----------------------------------------------------

        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        # En-tête
        titre = QLabel("CONTRÔLE AÉRIEN")
        titre.setStyleSheet("""
            QLabel {
                font-size: 19px;
                font-weight: bold;
                color: #f1f5f9;
                padding-bottom: 2px;
            }
        """)

        sous_titre = QLabel("SURVEILLANCE DU TRAFIC")
        sous_titre.setStyleSheet("""
            QLabel {
                font-size: 10px;
                font-weight: bold;
                color: #63788c;
                letter-spacing: 1px;
            }
        """)

        left_panel.addWidget(titre)
        left_panel.addWidget(sous_titre)

        # Informations
        info_group = QGroupBox("SYSTÈME")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        self.lbl_heure = QLabel("Heure : --:--:--")
        self.lbl_heure.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #dbeafe;
            }
        """)

        self.lbl_vent = QLabel("Vent : ---° / --- km/h")
        self.lbl_vent.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #9fb3c8;
            }
        """)

        self.lbl_stats = QLabel(f"Score : {self.engine.score}")
        self.lbl_stats.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #62d99b;
            }
        """)

        info_layout.addWidget(self.lbl_heure)
        info_layout.addWidget(self.lbl_vent)
        info_layout.addWidget(self.lbl_stats)

        info_group.setLayout(info_layout)
        left_panel.addWidget(info_group)

        # Liste des avions
        avions_group = QGroupBox("AVIONS EN VOL")
        avions_layout = QVBoxLayout()
        avions_layout.setContentsMargins(4, 8, 4, 4)

        self.list_avions = QListWidget()
        self.list_avions.setMinimumWidth(310)
        self.list_avions.setMinimumHeight(470)
        self.list_avions.itemClicked.connect(self._selection_via_liste)

        avions_layout.addWidget(self.list_avions)
        avions_group.setLayout(avions_layout)

        left_panel.addWidget(avions_group, 1)

        # ----------------------------------------------------
        # RADAR CENTRAL
        # ----------------------------------------------------

        radar_container = QFrame()
        radar_container.setStyleSheet("""
            QFrame {
                background-color: #0b1016;
                border: 1px solid #293440;
                border-radius: 10px;
            }
        """)

        radar_layout = QVBoxLayout(radar_container)
        radar_layout.setContentsMargins(5, 5, 5, 5)

        self.radar = RadarWidget(
            self.engine,
            self._selection_via_radar
        )

        radar_layout.addWidget(self.radar)

        # ----------------------------------------------------
        # PANNEAU DROIT
        # ----------------------------------------------------

        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)

        controls_group = QGroupBox("INSTRUCTIONS")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)

        # Avion sélectionné
        self.lbl_avion = QLabel("AUCUN AVION SÉLECTIONNÉ")
        self.lbl_avion.setAlignment(Qt.AlignCenter)

        self.lbl_avion.setStyleSheet("""
            QLabel {
                background-color: #111821;
                border: 1px solid #2c3743;
                border-radius: 6px;
                padding: 9px;
                color: #73879a;
                font-size: 11px;
                font-weight: bold;
            }
        """)

        # Cap
        self.lbl_cap = QLabel("CAP : ---°")
        self.lbl_cap.setAlignment(Qt.AlignCenter)

        self.lbl_cap.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #eaf2fa;
                padding: 8px;
            }
        """)

        self.cap_slider = QSlider(Qt.Horizontal)
        self.cap_slider.setRange(0, 359)
        self.cap_slider.setMinimumHeight(30)
        self.cap_slider.valueChanged.connect(self._cap_slider_change)

        lbl_astuce = QLabel(
            "← →  Modifier le cap\n"
            "↑ ↓  Modifier l'altitude"
        )

        lbl_astuce.setAlignment(Qt.AlignCenter)
        lbl_astuce.setStyleSheet("""
            QLabel {
                color: #718396;
                font-size: 10px;
                padding: 3px;
            }
        """)

        # Boutons
        btn_up = QPushButton("▲   MONTER")
        btn_up.setObjectName("btnMonter")
        btn_up.clicked.connect(lambda: self._executer(Monter))

        btn_down = QPushButton("▼   DESCENDRE")
        btn_down.setObjectName("btnDescendre")
        btn_down.clicked.connect(lambda: self._executer(Descendre))

        btn_land = QPushButton("▣   ATTERRIR")
        btn_land.setObjectName("btnAtterrir")
        btn_land.clicked.connect(lambda: self._executer(Atterrir))

        controls_layout.addWidget(self.lbl_avion)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(self.lbl_cap)
        controls_layout.addWidget(self.cap_slider)
        controls_layout.addWidget(lbl_astuce)
        controls_layout.addSpacing(8)
        controls_layout.addWidget(btn_up)
        controls_layout.addWidget(btn_down)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(btn_land)

        controls_group.setLayout(controls_layout)

        right_panel.addWidget(controls_group)
        right_panel.addStretch()

        # ----------------------------------------------------
        # ASSEMBLAGE
        # ----------------------------------------------------

        main_layout.addLayout(left_panel, 2)
        main_layout.addWidget(radar_container, 5)
        main_layout.addLayout(right_panel, 2)

        self.setCentralWidget(main_widget)

    # ========================================================
    # SÉLECTION
    # ========================================================

    def _selection_via_radar(self, avion):

        self.engine.selectionner(avion)
        self.avion_selectionne = avion

        self._synchroniser_slider(avion.cap)
        self._mettre_a_jour_avion_selectionne()

    def _selection_via_liste(self, item):

        name = item.text().split(" ")[0]

        for avion in self.engine.avions:
            if avion.name == name:
                self._selection_via_radar(avion)
                break

    def _mettre_a_jour_avion_selectionne(self):

        if not self.avion_selectionne:
            self.lbl_avion.setText("AUCUN AVION SÉLECTIONNÉ")
            self.lbl_avion.setStyleSheet("""
                QLabel {
                    background-color: #111821;
                    border: 1px solid #2c3743;
                    border-radius: 6px;
                    padding: 9px;
                    color: #73879a;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            return

        avion = self.avion_selectionne

        self.lbl_avion.setText(
            f"{avion.name}  •  ALT {int(avion.altitude)} m"
        )

        self.lbl_avion.setStyleSheet("""
            QLabel {
                background-color: #17283a;
                border: 1px solid #3c6a91;
                border-radius: 6px;
                padding: 9px;
                color: #9ed0ff;
                font-size: 11px;
                font-weight: bold;
            }
        """)

    # ========================================================
    # CAP
    # ========================================================

    def _synchroniser_slider(self, valeur_cap):

        self.cap_slider.blockSignals(True)
        self.cap_slider.setValue(int(valeur_cap))
        self.cap_slider.blockSignals(False)

        self.lbl_cap.setText(
            f"CAP : {int(valeur_cap):03d}°"
        )

    def _cap_slider_change(self, valeur):

        self.lbl_cap.setText(
            f"CAP : {valeur:03d}°"
        )

        if self.avion_selectionne:
            ChangerCap(
                self.avion_selectionne,
                valeur
            ).executer()

    # ========================================================
    # INSTRUCTIONS
    # ========================================================

    def _executer(self, classe_instruction):

        if not self.avion_selectionne:
            return

        if classe_instruction is Atterrir:

            piste = self.engine.piste_la_plus_proche(
                self.avion_selectionne
            )

            Atterrir(
                self.avion_selectionne,
                piste
            ).executer()

        else:
            classe_instruction(
                self.avion_selectionne
            ).executer()

    # ========================================================
    # CLAVIER
    # ========================================================

    def keyPressEvent(self, event):

        if self.avion_selectionne:

            if event.key() == Qt.Key_Left:
                self.avion_selectionne.ajuster_cap(-5)
                self._synchroniser_slider(
                    self.avion_selectionne.cap
                )
                return

            if event.key() == Qt.Key_Right:
                self.avion_selectionne.ajuster_cap(5)
                self._synchroniser_slider(
                    self.avion_selectionne.cap
                )
                return

            if event.key() == Qt.Key_Up:
                self.avion_selectionne.monter(100)
                return

            if event.key() == Qt.Key_Down:
                self.avion_selectionne.descendre(100)
                return

        super().keyPressEvent(event)

    # ========================================================
    # BOUCLE DE SIMULATION
    # ========================================================

    def _boucle_simulation(self):

        # Heure
        self.lbl_heure.setText(
            "Heure : " +
            QTime.currentTime().toString("HH:mm:ss")
        )

        # Vent
        self.lbl_vent.setText(
            f"Vent : "
            f"{self.engine.vent.direction:03d}° / "
            f"{self.engine.vent.vitesse} km/h"
        )

        # Simulation
        collision = self.engine.maj(0.1)

        # Vérification de la sélection
        if self.avion_selectionne not in self.engine.avions:
            self.avion_selectionne = None
            self._mettre_a_jour_avion_selectionne()

        # ----------------------------------------------------
        # LISTE DES AVIONS
        # ----------------------------------------------------

        self.list_avions.clear()

        for avion in self.engine.avions:

            texte = (
                f"{avion.name}   |   "
                f"ALT {int(avion.altitude)}m   |   "
                f"V {avion.vitesse}km/h   |   "
                f"FUEL {int(avion.fuel)}%"
            )

            self.list_avions.addItem(texte)

            item = self.list_avions.item(
                self.list_avions.count() - 1
            )

            if avion.selected:

                item.setBackground(
                    QColor(38, 59, 82)
                )

                item.setForeground(
                    QColor(230, 242, 255)
                )

            elif avion.en_alerte:

                item.setBackground(
                    QColor(90, 30, 30)
                )

                item.setForeground(
                    QColor(255, 205, 205)
                )

        # ----------------------------------------------------
        # STATUT
        # ----------------------------------------------------

        if collision:

            self.lbl_stats.setText(
                "⚠ COLLISION DÉTECTÉE !"
            )

            self.lbl_stats.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: bold;
                    color: #ff6262;
                }
            """)

        elif self.engine.dernier_evenement:

            self.lbl_stats.setText(
                f"Score : {self.engine.score}  •  "
                f"{self.engine.dernier_evenement}"
            )

            self.lbl_stats.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: bold;
                    color: #62d99b;
                }
            """)

        else:

            self.lbl_stats.setText(
                f"Score : {self.engine.score}"
            )

            self.lbl_stats.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: bold;
                    color: #62d99b;
                }
            """)

        # Informations avion sélectionné
        self._mettre_a_jour_avion_selectionne()

        # Radar
        self.radar.update()
