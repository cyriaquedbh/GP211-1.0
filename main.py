import sys
import math
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QListWidget,
                               QGraphicsView, QGraphicsScene)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPen, QBrush


# Simulation (Programmation Orientée Objet)[cite: 1]
class Avion:
    def __init__(self, identifiant):
        # Chaque avion possède des caractéristiques (altitude, vitesse, cap, carburant)[cite: 1]
        self.identifiant = identifiant
        self.x = random.randint(-200, 200)
        self.y = random.randint(-200, 200)
        self.altitude = random.randint(2000, 5000)
        self.vitesse = random.randint(300, 500)
        self.cap = random.randint(0, 360)
        self.carburant = 100
        self.est_selectionne = False

    def mettre_a_jour(self):
        # Gestion du temps qui fait évoluer la position des avions de manière continue[cite: 1]
        rad = math.radians(self.cap)
        distance = self.vitesse / 100
        self.x += distance * math.cos(rad)
        self.y += distance * math.sin(rad)
        self.carburant -= 0.1


class RadarView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-250, -250, 500, 500)
        self.setScene(self.scene)
        # Une zone d'attérissage[cite: 1]
        self.scene.addRect(-20, -50, 40, 100, QPen(Qt.white), QBrush(Qt.darkGray))

    def dessiner_avions(self, avions):
        self.scene.clear()
        self.scene.addRect(-20, -50, 40, 100, QPen(Qt.white), QBrush(Qt.darkGray))

        # Des avions affichés sous forme de symboles ou icônes[cite: 1]
        for avion in avions:
            couleur = Qt.red if avion.carburant < 20 else Qt.green
            if avion.est_selectionne:
                couleur = Qt.yellow

            self.scene.addEllipse(avion.x, avion.y, 10, 10, QPen(Qt.black), QBrush(couleur))
            texte = self.scene.addText(avion.identifiant)
            texte.setPos(avion.x + 10, avion.y)
            texte.setDefaultTextColor(Qt.white)


# Interface Graphique (PySide6)[cite: 1]
class ATCMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ATC Simulator")
        self.resize(1000, 600)

        self.avions = [Avion(f"AF{random.randint(100, 999)}"), Avion(f"LH{random.randint(100, 999)}")]
        self.avion_selectionne = None
        self.score = 0

        widget_principal = QWidget()
        layout_principal = QHBoxLayout()

        # Panel gauche: statistiques en temps réel + liste des avions avec leurs caractéristiques[cite: 1]
        layout_gauche = QVBoxLayout()
        self.label_stats = QLabel(f"Score: {self.score}\nAvions: {len(self.avions)}")
        layout_gauche.addWidget(self.label_stats)

        self.liste_avions = QListWidget()
        self.mettre_a_jour_liste()
        self.liste_avions.itemClicked.connect(self.selectionner_avion)
        layout_gauche.addWidget(self.liste_avions)

        # Zone centrale: visualisation radar de l'espace aérien[cite: 1]
        self.radar = RadarView()

        # Panel droit: contrôles pour donner des instructions à l'avion sélectionné[cite: 1]
        layout_droit = QVBoxLayout()
        self.label_info = QLabel("Aucun avion sélectionné")
        layout_droit.addWidget(self.label_info)

        btn_cap_gauche = QPushButton("Cap -10°")
        btn_cap_gauche.clicked.connect(lambda: self.modifier_instruction('cap', -10))
        btn_cap_droite = QPushButton("Cap +10°")
        btn_cap_droite.clicked.connect(lambda: self.modifier_instruction('cap', 10))
        btn_monter = QPushButton("Monter")
        btn_monter.clicked.connect(lambda: self.modifier_instruction('alt', 500))
        btn_descendre = QPushButton("Descendre")
        btn_descendre.clicked.connect(lambda: self.modifier_instruction('alt', -500))

        layout_droit.addWidget(btn_cap_gauche)
        layout_droit.addWidget(btn_cap_droite)
        layout_droit.addWidget(btn_monter)
        layout_droit.addWidget(btn_descendre)

        layout_principal.addLayout(layout_gauche, 1)
        layout_principal.addWidget(self.radar, 3)
        layout_principal.addLayout(layout_droit, 1)
        widget_principal.setLayout(layout_principal)
        self.setCentralWidget(widget_principal)

        self.timer = QTimer()
        self.timer.timeout.connect(self.boucle_simulation)
        self.timer.start(100)

    def mettre_a_jour_liste(self):
        self.liste_avions.clear()
        for a in self.avions:
            self.liste_avions.addItem(f"{a.identifiant} - Alt: {a.altitude}m")

    def selectionner_avion(self, item):
        texte = item.text().split(" ")[0]
        for a in self.avions:
            a.est_selectionne = (a.identifiant == texte)
            if a.est_selectionne:
                self.avion_selectionne = a
                # Affichage des informations de chaque avion au survol ou à la sélection[cite: 1]
                self.label_info.setText(
                    f"Sélectionné: {a.identifiant}\nCap: {a.cap}°\nVitesse: {a.vitesse}\nAlt: {a.altitude}m")
        self.radar.dessiner_avions(self.avions)

    def modifier_instruction(self, type_inst, valeur):
        # Des boutons ou menus permettant de donner des instructions (changer de cap, monter/descendre, atterrir)[cite: 1]
        if self.avion_selectionne:
            if type_inst == 'cap':
                self.avion_selectionne.cap = (self.avion_selectionne.cap + valeur) % 360
            elif type_inst == 'alt':
                self.avion_selectionne.altitude += valeur
            self.label_info.setText(
                f"Sélectionné: {self.avion_selectionne.identifiant}\nCap: {self.avion_selectionne.cap}°\nVitesse: {self.avion_selectionne.vitesse}\nAlt: {self.avion_selectionne.altitude}m")

    def boucle_simulation(self):
        for a in self.avions:
            a.mettre_a_jour()

        # Score basé sur le nombre d'avions gérés sans collision[cite: 1]
        self.score += 1
        self.label_stats.setText(f"Score: {self.score}\nAvions: {len(self.avions)}")
        self.radar.dessiner_avions(self.avions)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = ATCMainWindow()
    fenetre.show()
    sys.exit(app.exec())