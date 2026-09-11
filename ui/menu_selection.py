from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from config.airports import AEROPORTS_DISPONIBLES

STYLE_DIALOG = """
QDialog {
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
    margin-top: 10px;
    padding: 14px 12px 12px 12px;
}

QComboBox {
    background-color: #0d121d;
    border: 1px solid #222f43;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f8fafc;
    font-size: 13px;
    font-weight: 600;
}

QComboBox:hover {
    border-color: #38bdf8;
    background-color: #161f2e;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #121824;
    border: 1px solid #1e293b;
    selection-background-color: #1e3a5f;
    selection-color: #38bdf8;
    color: #cbd5e1;
    padding: 4px;
    outline: none;
}

QPushButton#btnDemarrer {
    background-color: #0284c7;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 10px 16px;
    min-height: 36px;
}

QPushButton#btnDemarrer:hover {
    background-color: #0369a1;
    border-color: #7dd3fc;
}

QPushButton#btnDemarrer:pressed {
    background-color: #075985;
}
"""


class MenuSelectionAeroport(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ATC Command — Sélection du Secteur")
        self.setFixedSize(440, 360)
        self.setStyleSheet(STYLE_DIALOG)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # En-tête
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        titre = QLabel("AIR TRAFFIC CONTROL")
        titre.setStyleSheet(
            "font-size: 18px; font-weight: 900; color: #f8fafc; letter-spacing: 1.5px;"
        )

        sous_titre = QLabel("INITIALISATION DU SECTEUR DE CONTRÔLE")
        sous_titre.setStyleSheet(
            "font-size: 10px; font-weight: 800; color: #0284c7; letter-spacing: 1.5px;"
        )

        header_layout.addWidget(titre)
        header_layout.addWidget(sous_titre)
        layout.addLayout(header_layout)

        # Groupe Sélection
        group_box = QGroupBox()
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(12)

        lbl_select = QLabel("AÉROPORT D'AFFECTATION")
        lbl_select.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 1px;"
        )

        self.combo = QComboBox()
        for aeroport in AEROPORTS_DISPONIBLES:
            self.combo.addItem(
                f"✈  {aeroport.nom} ({aeroport.code_iata})", aeroport
            )

        # Panneau détails aéroport
        details_frame = QFrame()
        details_frame.setStyleSheet(
            "background-color: #0d121d; border: 1px solid #1e293b; border-radius: 6px; padding: 10px;"
        )
        details_layout = QVBoxLayout(details_frame)
        details_layout.setSpacing(6)

        self.lbl_icao = QLabel("ICAO : ----")
        self.lbl_icao.setStyleSheet(
            "font-size: 11px; font-family: 'Consolas', monospace; color: #38bdf8; font-weight: 700;"
        )

        self.lbl_pistes = QLabel("PISTES : --")
        self.lbl_pistes.setStyleSheet(
            "font-size: 11px; font-family: 'Consolas', monospace; color: #94a3b8;"
        )
        self.lbl_pistes.setWordWrap(True)

        details_layout.addWidget(self.lbl_icao)
        details_layout.addWidget(self.lbl_pistes)

        group_layout.addWidget(lbl_select)
        group_layout.addWidget(self.combo)
        group_layout.addWidget(details_frame)

        layout.addWidget(group_box)

        # Signal connexion
        self.combo.currentIndexChanged.connect(self._maj_details)
        self._maj_details()

        layout.addStretch()

        # Bouton Démarrer
        btn_valider = QPushButton("DÉMARRER LA SIMULATION  ►")
        btn_valider.setObjectName("btnDemarrer")
        btn_valider.setCursor(Qt.PointingHandCursor)
        btn_valider.clicked.connect(self.accept)
        layout.addWidget(btn_valider)

    def _maj_details(self):
        aeroport = self.combo.currentData()
        if aeroport:
            self.lbl_icao.setText(
                f"INDICATIF : {aeroport.code_icao} / {aeroport.code_iata}"
            )
            pistes_str = ", ".join(p.nom for p in aeroport.pistes)
            self.lbl_pistes.setText(f"PISTES ACTIVES : {pistes_str}")

    def get_aeroport_selectionne(self):
        return self.combo.currentData()