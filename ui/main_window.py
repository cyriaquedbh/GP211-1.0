from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QListWidget, QSpinBox, QGroupBox)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

from controllers.simulation_engine import SimulationEngine
from controllers.instructions import ChangerCap, Monter, Descendre, Atterrir
from ui.radar_widget import RadarWidget


class SimulateurATC(QMainWindow):
    def __init__(self, aeroport):
        super().__init__()
        self.setWindowTitle(f"Simulateur ATC - {aeroport.nom}")
        self.engine = SimulationEngine(aeroport)
        self.avion_selectionne = None

        self._init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self._boucle_simulation)
        self.timer.start(50)

    def _init_ui(self):
        main_widget = QWidget()
        layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        self.lbl_stats = QLabel(f"Score: {self.engine.score}")
        self.list_avions = QListWidget()
        self.list_avions.itemClicked.connect(self._selection_via_liste)
        left_panel.addWidget(self.lbl_stats)
        left_panel.addWidget(QLabel("AVIONS EN VOL:"))
        left_panel.addWidget(self.list_avions)

        self.radar = RadarWidget(self.engine, self._selection_via_radar)

        right_panel = QVBoxLayout()
        controls_group = QGroupBox("INSTRUCTIONS")
        controls_layout = QVBoxLayout()

        self.cap_spin = QSpinBox()
        self.cap_spin.setRange(0, 359)
        self.cap_spin.setPrefix("Cap: ")

        btn_apply = QPushButton("Changer de cap")
        btn_apply.clicked.connect(self._changer_cap)
        btn_up = QPushButton("Monter (+500m)")
        btn_up.clicked.connect(lambda: self._executer(Monter))
        btn_down = QPushButton("Descendre (-500m)")
        btn_down.clicked.connect(lambda: self._executer(Descendre))
        btn_land = QPushButton("Atterrir")
        btn_land.clicked.connect(lambda: self._executer(Atterrir))

        for w in (self.cap_spin, btn_apply, btn_up, btn_down, btn_land):
            controls_layout.addWidget(w)
        controls_group.setLayout(controls_layout)
        right_panel.addWidget(controls_group)
        right_panel.addStretch()

        layout.addLayout(left_panel, 1)
        layout.addWidget(self.radar, 3)
        layout.addLayout(right_panel, 1)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def _selection_via_radar(self, avion):
        self.engine.selectionner(avion)
        self.avion_selectionne = avion
        self.cap_spin.setValue(int(avion.cap))

    def _selection_via_liste(self, item):
        name = item.text().split(" ")[0]
        for a in self.engine.avions:
            if a.name == name:
                self._selection_via_radar(a)
                break

    def _changer_cap(self):
        if self.avion_selectionne:
            ChangerCap(self.avion_selectionne, self.cap_spin.value()).executer()

    def _executer(self, classe_instruction):
        if self.avion_selectionne:
            classe_instruction(self.avion_selectionne).executer()

    def _boucle_simulation(self):
        collision = self.engine.maj(0.1)

        if self.avion_selectionne not in self.engine.avions:
            self.avion_selectionne = None

        self.list_avions.clear()
        for a in self.engine.avions:
            self.list_avions.addItem(
                f"{a.name} - Alt: {int(a.altitude)}m - V: {a.vitesse}km/h - Fuel: {int(a.fuel)}%")
            if a.selected:
                self.list_avions.item(self.list_avions.count() - 1).setBackground(QColor(70, 70, 100))

        if collision:
            self.lbl_stats.setText("COLLISION DÉTECTÉE !")
            self.lbl_stats.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.lbl_stats.setText(f"Score: {self.engine.score}")
            self.lbl_stats.setStyleSheet("color: #00FF00; font-weight: bold;")

        self.radar.update()