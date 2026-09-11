from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QListWidget, QSlider, QGroupBox)
from PySide6.QtCore import QTimer, Qt, QTime
from PySide6.QtGui import QColor, QFont

from controllers.simulation_engine import SimulationEngine
from controllers.instructions import ChangerCap, Monter, Descendre, Atterrir
from ui.radar_widget import RadarWidget


STYLE_BOUTON = """
QPushButton {
    font-size: 13px;
    padding: 6px;
    min-height: 30px;
}
"""

STYLE_LISTE = """
QListWidget {
    font-size: 14px;
}
QListWidget::item {
    padding: 6px;
}
"""


class SimulateurATC(QMainWindow):
    def __init__(self, aeroport):
        super().__init__()
        self.setWindowTitle(f"Simulateur ATC - {aeroport.nom}")
        self.engine = SimulationEngine(aeroport)
        self.avion_selectionne = None

        self._init_ui()
        self.setFocusPolicy(Qt.StrongFocus)

        self.timer = QTimer()
        self.timer.timeout.connect(self._boucle_simulation)
        self.timer.start(50)

    def _init_ui(self):
        main_widget = QWidget()
        layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        font_info = QFont()
        font_info.setPointSize(11)
        font_info.setBold(True)

        self.lbl_heure = QLabel()
        self.lbl_heure.setFont(font_info)
        self.lbl_stats = QLabel(f"Score: {self.engine.score}")
        self.lbl_stats.setFont(font_info)
        self.lbl_vent = QLabel()
        self.lbl_vent.setFont(font_info)

        lbl_titre_liste = QLabel("AVIONS EN VOL :")
        lbl_titre_liste.setFont(font_info)

        self.list_avions = QListWidget()
        self.list_avions.setMinimumWidth(280)
        self.list_avions.setMinimumHeight(500)
        self.list_avions.setStyleSheet(STYLE_LISTE)
        self.list_avions.itemClicked.connect(self._selection_via_liste)

        left_panel.addWidget(self.lbl_heure)
        left_panel.addWidget(self.lbl_stats)
        left_panel.addWidget(self.lbl_vent)
        left_panel.addWidget(lbl_titre_liste)
        left_panel.addWidget(self.list_avions)

        self.radar = RadarWidget(self.engine, self._selection_via_radar)

        right_panel = QVBoxLayout()
        controls_group = QGroupBox("INSTRUCTIONS")
        controls_group.setMinimumWidth(230)
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)

        self.lbl_cap = QLabel("Cap : --")
        self.lbl_cap.setFont(font_info)
        self.lbl_cap.setAlignment(Qt.AlignCenter)

        self.cap_slider = QSlider(Qt.Horizontal)
        self.cap_slider.setRange(0, 359)
        self.cap_slider.setMinimumHeight(30)
        self.cap_slider.valueChanged.connect(self._cap_slider_change)

        lbl_astuce = QLabel("Flèches ← → : cap  |  ↑ ↓ : altitude")
        lbl_astuce.setStyleSheet("font-size: 10px; color: gray;")
        lbl_astuce.setWordWrap(True)

        btn_up = QPushButton("⬆ Monter (+500m)")
        btn_up.setStyleSheet(STYLE_BOUTON)
        btn_up.clicked.connect(lambda: self._executer(Monter))

        btn_down = QPushButton("⬇ Descendre (-500m)")
        btn_down.setStyleSheet(STYLE_BOUTON)
        btn_down.clicked.connect(lambda: self._executer(Descendre))

        btn_land = QPushButton("🛬 Atterrir")
        btn_land.setStyleSheet(STYLE_BOUTON)
        btn_land.clicked.connect(lambda: self._executer(Atterrir))

        controls_layout.addWidget(self.lbl_cap)
        controls_layout.addWidget(self.cap_slider)
        controls_layout.addWidget(lbl_astuce)
        controls_layout.addWidget(btn_up)
        controls_layout.addWidget(btn_down)
        controls_layout.addWidget(btn_land)
        controls_group.setLayout(controls_layout)
        right_panel.addWidget(controls_group)
        right_panel.addStretch()

        layout.addLayout(left_panel, 2)
        layout.addWidget(self.radar, 4)
        layout.addLayout(right_panel, 2)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def _selection_via_radar(self, avion):
        self.engine.selectionner(avion)
        self.avion_selectionne = avion
        self._synchroniser_slider(avion.cap)

    def _selection_via_liste(self, item):
        name = item.text().split(" ")[0]
        for a in self.engine.avions:
            if a.name == name:
                self._selection_via_radar(a)
                break

    def _synchroniser_slider(self, valeur_cap):
        self.cap_slider.blockSignals(True)
        self.cap_slider.setValue(int(valeur_cap))
        self.cap_slider.blockSignals(False)
        self.lbl_cap.setText(f"Cap : {int(valeur_cap):03d}°")

    def _cap_slider_change(self, valeur):
        self.lbl_cap.setText(f"Cap : {valeur:03d}°")
        if self.avion_selectionne:
            ChangerCap(self.avion_selectionne, valeur).executer()

    def _executer(self, classe_instruction):
        if not self.avion_selectionne:
            return
        if classe_instruction is Atterrir:
            piste = self.engine.piste_la_plus_proche(self.avion_selectionne)
            Atterrir(self.avion_selectionne, piste).executer()
        else:
            classe_instruction(self.avion_selectionne).executer()

    def keyPressEvent(self, event):
        if self.avion_selectionne:
            if event.key() == Qt.Key_Left:
                self.avion_selectionne.ajuster_cap(-5)
                self._synchroniser_slider(self.avion_selectionne.cap)
                return
            if event.key() == Qt.Key_Right:
                self.avion_selectionne.ajuster_cap(5)
                self._synchroniser_slider(self.avion_selectionne.cap)
                return
            if event.key() == Qt.Key_Up:
                self.avion_selectionne.monter(100)
                return
            if event.key() == Qt.Key_Down:
                self.avion_selectionne.descendre(100)
                return
        super().keyPressEvent(event)

    def _boucle_simulation(self):
        self.lbl_heure.setText("Heure : " + QTime.currentTime().toString("HH:mm:ss"))
        self.lbl_vent.setText(f"Vent : {self.engine.vent.direction:03d}° / {self.engine.vent.vitesse} km/h")

        collision = self.engine.maj(0.1)

        if self.avion_selectionne not in self.engine.avions:
            self.avion_selectionne = None

        self.list_avions.clear()
        for a in self.engine.avions:
            self.list_avions.addItem(
                f"{a.name}  |  Alt: {int(a.altitude)}m  |  V: {a.vitesse}km/h  |  Fuel: {int(a.fuel)}%")
            if a.selected:
                self.list_avions.item(self.list_avions.count() - 1).setBackground(QColor(70, 70, 100))
            elif a.en_alerte:
                self.list_avions.item(self.list_avions.count() - 1).setBackground(QColor(120, 0, 0))

        if collision:
            self.lbl_stats.setText("COLLISION DÉTECTÉE !")
            self.lbl_stats.setStyleSheet("color: red; font-weight: bold;")
        elif self.engine.dernier_evenement:
            self.lbl_stats.setText(f"Score: {self.engine.score} - {self.engine.dernier_evenement}")
            self.lbl_stats.setStyleSheet("color: #00FF00; font-weight: bold;")
        else:
            self.lbl_stats.setText(f"Score: {self.engine.score}")
            self.lbl_stats.setStyleSheet("color: #00FF00; font-weight: bold;")

        self.radar.update()