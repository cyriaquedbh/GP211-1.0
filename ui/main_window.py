from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QSlider, QGroupBox,
    QFrame, QListWidgetItem
)
from PySide6.QtCore import QTimer, Qt, QTime
from PySide6.QtGui import QColor, QFont

from controllers.simulation_engine import SimulationEngine
from controllers.instructions import ChangerCap, Monter, Descendre, Atterrir, Attendre
from ui.radar_widget import RadarWidget
from ui.cockpit_widget import CockpitWidget


STYLE_GLOBAL = """
QMainWindow {
    background-color: #0b0f17;
}

QWidget {
    color: #c5d1de;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

QGroupBox {
    background-color: #121824;
    border: 1px solid #1e293b;
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    color: #64748b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    background-color: #121824;
    color: #38bdf8;
    text-transform: uppercase;
}

QLabel {
    color: #cbd5e1;
}

QListWidget {
    background-color: #0d121d;
    border: 1px solid #1e293b;
    border-radius: 8px;
    outline: none;
    padding: 6px;
    font-size: 12px;
}

QListWidget::item {
    background-color: #161f2e;
    border: 1px solid #222f43;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 6px;
    color: #94a3b8;
}

QListWidget::item:hover {
    background-color: #1e2a3e;
    border-color: #3b82f6;
    color: #f8fafc;
}

QListWidget::item:selected {
    background-color: #1e3a5f;
    border: 1px solid #38bdf8;
    color: #ffffff;
}

QSlider::groove:horizontal {
    height: 8px;
    background: #162032;
    border: 1px solid #26334d;
    border-radius: 4px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 4px;
}

QSlider::handle:horizontal {
    width: 20px;
    height: 20px;
    margin: -6px 0;
    background: #f8fafc;
    border: 2px solid #38bdf8;
    border-radius: 10px;
}

QPushButton {
    background-color: #162235;
    border: 1px solid #25354e;
    border-radius: 6px;
    color: #e2e8f0;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 10px 14px;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #1d2d47;
    border-color: #38bdf8;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton#btnMonter {
    border-left: 3px solid #10b981;
}

QPushButton#btnMonter:hover {
    background-color: #064e3b;
    border-color: #10b981;
}

QPushButton#btnDescendre {
    border-left: 3px solid #f59e0b;
}

QPushButton#btnDescendre:hover {
    background-color: #78350f;
    border-color: #f59e0b;
}

QPushButton#btnAtterrir {
    background-color: #064e3b;
    border: 1px solid #059669;
    color: #a7f3d0;
}

QPushButton#btnAtterrir:hover {
    background-color: #047857;
    border-color: #34d399;
    color: #ffffff;
}

QPushButton#btnAttente {
    background-color: #431407;
    border: 1px solid #ea580c;
    color: #ffedd5;
}

QPushButton#btnAttente:hover {
    background-color: #7c2d12;
    border-color: #f97316;
    color: #ffffff;
}

QPushButton#btnCockpit {
    background-color: #1e1b4b;
    border: 1px solid #6366f1;
    color: #c7d2fe;
}

QPushButton#btnCockpit:hover {
    background-color: #312e81;
    border-color: #818cf8;
    color: #ffffff;
}
"""


class SimulateurATC(QMainWindow):

    def __init__(self, aeroport):
        super().__init__()

        self.setWindowTitle(f"ATC Radar Command — {aeroport.nom}")
        self.setMinimumSize(1280, 760)

        self.engine = SimulationEngine(aeroport)
        self.avion_selectionne = None
        self.cockpit_dialog = None

        self.setStyleSheet(STYLE_GLOBAL)
        self.setFocusPolicy(Qt.StrongFocus)

        self._init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self._boucle_simulation)
        self.timer.start(50)

    def _init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        titre = QLabel("AIR TRAFFIC CONTROL")
        titre.setStyleSheet("font-size: 18px; font-weight: 900; color: #f8fafc; letter-spacing: 1.5px;")

        sous_titre = QLabel("MONITORING SYSTEM")
        sous_titre.setStyleSheet("font-size: 10px; font-weight: 800; color: #0284c7; letter-spacing: 2px;")

        header_layout.addWidget(titre)
        header_layout.addWidget(sous_titre)
        left_panel.addLayout(header_layout)

        info_group = QGroupBox("TÉLÉMÉTRIE SYSTÈME")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        self.lbl_heure = QLabel("UTC : --:--:--")
        self.lbl_heure.setStyleSheet("font-size: 13px; font-weight: 700; font-family: 'Consolas', monospace; color: #38bdf8; background-color: #0f172a; padding: 6px 10px; border-radius: 4px; border: 1px solid #1e293b;")

        self.lbl_vent = QLabel("VENT : ---° / --- km/h")
        self.lbl_vent.setStyleSheet("font-size: 11px; font-weight: 600; font-family: 'Consolas', monospace; color: #94a3b8; background-color: #0f172a; padding: 6px 10px; border-radius: 4px; border: 1px solid #1e293b;")

        self.lbl_stats = QLabel(f"SCORE : {self.engine.score}")
        self.lbl_stats.setStyleSheet("font-size: 12px; font-weight: 800; color: #34d399; background-color: #064e3b; padding: 8px 10px; border-radius: 4px; border: 1px solid #059669;")

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
        radar_container.setStyleSheet("QFrame { background-color: #05080c; border: 1px solid #1e293b; border-radius: 12px; }")
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
        self.lbl_avion.setStyleSheet("background-color: #0f172a; border: 1px dashed #334155; border-radius: 6px; padding: 12px; color: #64748b; font-size: 11px; font-weight: 800;")

        self.lbl_cap = QLabel("CAP : ---°")
        self.lbl_cap.setAlignment(Qt.AlignCenter)
        self.lbl_cap.setStyleSheet("font-size: 26px; font-weight: 900; font-family: 'Consolas', monospace; color: #f8fafc; background-color: #090d14; border: 1px solid #1e293b; border-radius: 6px; padding: 10px;")

        self.cap_slider = QSlider(Qt.Horizontal)
        self.cap_slider.setRange(0, 359)
        self.cap_slider.setMinimumHeight(30)
        self.cap_slider.valueChanged.connect(self._cap_slider_change)

        lbl_astuce = QLabel("RACCOURCIS CLAVIER (Maintien fluide)\n◄ / ► : Ajuster le cap\n▲ / ▼ : Ajuster l'altitude")
        lbl_astuce.setAlignment(Qt.AlignCenter)
        lbl_astuce.setStyleSheet("color: #475569; font-size: 10px; font-weight: 600; background-color: #0f172a; border-radius: 4px; padding: 6px;")

        btn_up = QPushButton("▲   MONTER  (+100m)")
        btn_up.setObjectName("btnMonter")
        btn_up.clicked.connect(lambda: self._executer(Monter))

        btn_down = QPushButton("▼   DESCENDRE  (-100m)")
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

        controls_group.setLayout(controls_layout)
        right_panel.addWidget(controls_group)
        right_panel.addStretch()

        main_layout.addLayout(left_panel, 2)
        main_layout.addWidget(radar_container, 5)
        main_layout.addLayout(right_panel, 2)

        self.setCentralWidget(main_widget)

    def _selection_via_radar(self, avion):
        self.engine.selectionner(avion)
        self.avion_selectionne = avion
        self._synchroniser_slider(avion.target_cap)
        self._mettre_a_jour_avion_selectionne()

    def _selection_via_liste(self, item):
        name = item.text().split("\n")[0].replace("✈ ", "").strip()
        for avion in self.engine.avions:
            if avion.name == name:
                self._selection_via_radar(avion)
                break

    def _mettre_a_jour_avion_selectionne(self):
        if not self.avion_selectionne:
            self.lbl_avion.setText("AUCUNE CIBLE SÉLECTIONNÉE")
            self.lbl_avion.setStyleSheet("background-color: #0f172a; border: 1px dashed #334155; border-radius: 6px; padding: 12px; color: #64748b; font-size: 11px; font-weight: 800;")
            return

        avion = self.avion_selectionne
        statut = " [HOLDING]" if avion.is_holding else ""
        self.lbl_avion.setText(f"✈ {avion.name}{statut}\nALTITUDE: {int(avion.altitude)} m")
        self.lbl_avion.setStyleSheet("background-color: #0c4a6e; border: 1px solid #38bdf8; border-radius: 6px; padding: 10px; color: #f0f9ff; font-size: 12px; font-weight: 800;")

    def _synchroniser_slider(self, valeur_cap):
        self.cap_slider.blockSignals(True)
        self.cap_slider.setValue(int(valeur_cap))
        self.cap_slider.blockSignals(False)
        self.lbl_cap.setText(f"CAP : {int(valeur_cap):03d}°")

    def _cap_slider_change(self, valeur):
        self.lbl_cap.setText(f"CAP : {valeur:03d}°")
        if self.avion_selectionne:
            ChangerCap(self.avion_selectionne, valeur).executer()

    def _executer(self, classe_instruction):
        if not self.avion_selectionne:
            return

        if classe_instruction is Atterrir:
            piste = self.engine.piste_la_plus_proche(self.avion_selectionne)
            Atterrir(self.avion_selectionne, piste).executer()
        elif classe_instruction is Attendre:
            Attendre(self.avion_selectionne).executer()
        elif classe_instruction in (Monter, Descendre):
            classe_instruction(self.avion_selectionne, delta=100).executer()
        else:
            classe_instruction(self.avion_selectionne).executer()

    def _ouvrir_vue_cockpit(self):
        if self.avion_selectionne:
            self.cockpit_dialog = CockpitWidget(
                self.avion_selectionne, self.engine, self
            )
            self.cockpit_dialog.show()

    def keyPressEvent(self, event):
        if self.avion_selectionne:
            if event.key() == Qt.Key_Left:
                self.avion_selectionne.ajuster_cap(-2)
                self._synchroniser_slider(self.avion_selectionne.target_cap)
                return

            if event.key() == Qt.Key_Right:
                self.avion_selectionne.ajuster_cap(2)
                self._synchroniser_slider(self.avion_selectionne.target_cap)
                return

            if event.key() == Qt.Key_Up:
                self.avion_selectionne.monter(50)
                return

            if event.key() == Qt.Key_Down:
                self.avion_selectionne.descendre(50)
                return

        super().keyPressEvent(event)

    def _boucle_simulation(self):
        self.lbl_heure.setText("UTC : " + QTime.currentTime().toString("HH:mm:ss"))
        self.lbl_vent.setText(f"VENT : {self.engine.vent.direction:03d}° / {self.engine.vent.vitesse} km/h")

        collision = self.engine.maj(0.1)

        if self.avion_selectionne not in self.engine.avions:
            self.avion_selectionne = None
            self._mettre_a_jour_avion_selectionne()
        else:
            self._synchroniser_slider(self.avion_selectionne.target_cap)

        self.list_avions.clear()
        for avion in self.engine.avions:
            texte_carte = (
                f"✈ {avion.name}\n"
                f"ALT : {int(avion.altitude)} m   |   SPD : {avion.vitesse} km/h\n"
                f"CAP : {int(avion.cap):03d}°    |   FUEL : {int(avion.fuel)}%"
            )
            item = QListWidgetItem(texte_carte)
            item.setFont(QFont("Consolas", 9))
            self.list_avions.addItem(item)

            if avion.selected:
                item.setBackground(QColor(14, 116, 144))
                item.setForeground(QColor(255, 255, 255))
            elif avion.en_alerte:
                item.setBackground(QColor(127, 29, 29))
                item.setForeground(QColor(254, 202, 202))

        if collision:
            self.lbl_stats.setText("⚠ COLLISION DÉTECTÉE !")
            self.lbl_stats.setStyleSheet("font-size: 12px; font-weight: 800; color: #fca5a5; background-color: #7f1d1d; padding: 8px 10px; border-radius: 4px; border: 1px solid #ef4444;")
        elif self.engine.dernier_evenement:
            self.lbl_stats.setText(f"SCORE : {self.engine.score}  •  {self.engine.dernier_evenement}")
            self.lbl_stats.setStyleSheet("font-size: 12px; font-weight: 800; color: #34d399; background-color: #064e3b; padding: 8px 10px; border-radius: 4px; border: 1px solid #059669;")
        else:
            self.lbl_stats.setText(f"SCORE : {self.engine.score}")
            self.lbl_stats.setStyleSheet("font-size: 12px; font-weight: 800; color: #34d399; background-color: #064e3b; padding: 8px 10px; border-radius: 4px; border: 1px solid #059669;")

        self._mettre_a_jour_avion_selectionne()
        self.radar.update()

        if self.cockpit_dialog and self.cockpit_dialog.isVisible():
            self.cockpit_dialog.update()