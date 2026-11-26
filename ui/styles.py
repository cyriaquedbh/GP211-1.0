"""Styles Qt de l'interface principale (feuille globale + styles des libellés dynamiques)."""

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

# ---------------------------------------------------------------- libellés

STYLE_TITRE = "font-size: 18px; font-weight: 900; color: #f8fafc; letter-spacing: 1.5px;"
STYLE_SOUS_TITRE = "font-size: 10px; font-weight: 800; color: #0284c7; letter-spacing: 2px;"

_MONO_PANNEAU = (
    "font-family: 'Consolas', monospace; background-color: #0f172a; "
    "padding: 6px 10px; border-radius: 4px; border: 1px solid #1e293b;"
)
STYLE_HEURE = f"font-size: 13px; font-weight: 700; color: #38bdf8; {_MONO_PANNEAU}"
STYLE_VENT = f"font-size: 11px; font-weight: 600; color: #94a3b8; {_MONO_PANNEAU}"

_STATS = "font-size: 12px; font-weight: 800; padding: 8px 10px; border-radius: 4px;"
STYLE_STATS_OK = f"{_STATS} color: #34d399; background-color: #064e3b; border: 1px solid #059669;"
STYLE_STATS_ALERTE = f"{_STATS} color: #fca5a5; background-color: #7f1d1d; border: 1px solid #ef4444;"

STYLE_AVION_VIDE = (
    "background-color: #0f172a; border: 1px dashed #334155; border-radius: 6px; "
    "padding: 12px; color: #64748b; font-size: 11px; font-weight: 800;"
)
STYLE_AVION_ACTIF = (
    "background-color: #0c4a6e; border: 1px solid #38bdf8; border-radius: 6px; "
    "padding: 10px; color: #f0f9ff; font-size: 12px; font-weight: 800;"
)
STYLE_CAP = (
    "font-size: 26px; font-weight: 900; font-family: 'Consolas', monospace; color: #f8fafc; "
    "background-color: #090d14; border: 1px solid #1e293b; border-radius: 6px; padding: 10px;"
)
STYLE_ASTUCE = (
    "color: #475569; font-size: 10px; font-weight: 600; background-color: #0f172a; "
    "border-radius: 4px; padding: 6px;"
)
STYLE_RADAR_CONTENEUR = (
    "QFrame { background-color: #05080c; border: 1px solid #1e293b; border-radius: 12px; }"
)

_RETOUR = "border-radius: 6px; padding: 6px; font-size: 11px; font-weight: 700;"
STYLE_RETOUR_VIDE = "background-color: transparent; border: none; padding: 6px;"
STYLE_RETOUR_OK = f"{_RETOUR} color: #a7f3d0; background-color: #064e3b; border: 1px solid #059669;"
STYLE_RETOUR_ERREUR = f"{_RETOUR} color: #fde68a; background-color: #78350f; border: 1px solid #f59e0b;"
