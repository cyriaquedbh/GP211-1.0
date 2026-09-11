from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from config.airports import AEROPORTS_DISPONIBLES


class MenuSelectionAeroport(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulateur ATC - Choix de l'aéroport")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Sélectionnez un aéroport :"))

        self.combo = QComboBox()
        for aeroport in AEROPORTS_DISPONIBLES:
            self.combo.addItem(f"{aeroport.nom} ({aeroport.code_iata})", aeroport)
        layout.addWidget(self.combo)

        self.lbl_pistes = QLabel()
        layout.addWidget(self.lbl_pistes)
        self.combo.currentIndexChanged.connect(self._maj_pistes)
        self._maj_pistes()

        btn_valider = QPushButton("Démarrer la simulation")
        btn_valider.clicked.connect(self.accept)
        layout.addWidget(btn_valider)

        self.setLayout(layout)

    def _maj_pistes(self):
        aeroport = self.combo.currentData()
        self.lbl_pistes.setText("Pistes : " + ", ".join(p.nom for p in aeroport.pistes))

    def get_aeroport_selectionne(self):
        return self.combo.currentData()