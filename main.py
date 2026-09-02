import sys
import math
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QListWidget,
                               QSpinBox, QGroupBox)
from PySide6.QtCore import QTimer, Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF


class Avion:
    def __init__(self, name):
        self.name = name
        self.x = random.uniform(50, 550)
        self.y = random.uniform(50, 550)
        self.altitude = random.randint(2000, 5000)
        self.target_altitude = self.altitude
        self.vitesse = random.randint(300, 500)
        self.cap = random.randint(0, 359)
        self.fuel = 100.0
        self.selected = False
        self.is_landing = False

    def update(self, dt):
        if self.altitude < self.target_altitude:
            self.altitude += min(20, self.target_altitude - self.altitude)
        elif self.altitude > self.target_altitude:
            self.altitude -= min(20, self.altitude - self.target_altitude)

        if self.is_landing:
            dx = 300 - self.x
            dy = 300 - self.y
            angle = math.degrees(math.atan2(dx, -dy)) % 360

            diff = (angle - self.cap + 180) % 360 - 180
            if abs(diff) > 2:
                self.cap += 2 if diff > 0 else -2
            self.cap %= 360

        rad = math.radians(self.cap)
        self.x += math.sin(rad) * (self.vitesse / 100) * dt
        self.y -= math.cos(rad) * (self.vitesse / 100) * dt
        self.fuel -= 0.1 * dt


class Radar(QWidget):
    def __init__(self, sim):
        super().__init__()
        self.sim = sim
        self.setMinimumSize(600, 600)
        self.setStyleSheet("background-color: #001100;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.save()
        painter.translate(300, 300)
        painter.rotate(self.sim.piste_angle)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(50, 50, 50))
        painter.drawRect(-20, -150, 40, 300)

        pen = QPen(QColor(255, 255, 255), 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(0, -140, 0, 140)

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        for x_offset in range(-15, 16, 5):
            painter.drawLine(x_offset, -145, x_offset, -135)
            painter.drawLine(x_offset, 135, x_offset, 145)

        font = painter.font()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)

        cap_bot = int(self.sim.piste_angle / 10)
        cap_top = int((self.sim.piste_angle + 180) % 360 / 10)
        if cap_bot == 0: cap_bot = 36
        if cap_top == 0: cap_top = 36

        lbl_top = f"{cap_top:02d}"
        lbl_bot = f"{cap_bot:02d}"

        painter.drawText(-7, -115, lbl_top)

        painter.save()
        painter.translate(0, 115)
        painter.rotate(180)
        painter.drawText(-7, 0, lbl_bot)
        painter.restore()

        painter.restore()

        for avion in self.sim.avions:
            painter.save()
            painter.translate(avion.x, avion.y)
            painter.rotate(avion.cap - 90)

            poly = QPolygonF([
                QPointF(12, 0),
                QPointF(-8, -10),
                QPointF(-4, 0),
                QPointF(-8, 10)
            ])

            color = QColor(255, 50, 50) if avion.selected else QColor(50, 255, 255)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawPolygon(poly)
            painter.restore()

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(avion.x + 10), int(avion.y - 10), f"{avion.name} ({avion.altitude}m)")

    def mousePressEvent(self, event):
        click_x = event.position().x()
        click_y = event.position().y()
        for avion in self.sim.avions:
            if math.hypot(avion.x - click_x, avion.y - click_y) < 15:
                for a in self.sim.avions:
                    a.selected = False
                avion.selected = True
                self.sim.selected_avion = avion
                self.sim.cap_spin.setValue(avion.cap)
                break


class SimulateurATC(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projet Python - IPSA - Simulateur de tour de contrôle")
        self.avions = []
        self.score = 0
        self.selected_avion = None
        self.piste_angle = random.randint(0, 359)

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sim)
        self.timer.start(50)

        for i in range(3):
            self.avions.append(Avion(f"AF10{i}"))

    def init_ui(self):
        main_widget = QWidget()
        layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        self.lbl_stats = QLabel(f"Score: {self.score}")
        self.list_avions = QListWidget()
        self.list_avions.itemClicked.connect(self.select_avion_list)
        left_panel.addWidget(self.lbl_stats)
        left_panel.addWidget(QLabel("AVIONS EN VOL:"))
        left_panel.addWidget(self.list_avions)

        self.radar = Radar(self)

        right_panel = QVBoxLayout()
        controls_group = QGroupBox("INSTRUCTIONS")
        controls_layout = QVBoxLayout()

        self.cap_spin = QSpinBox()
        self.cap_spin.setRange(0, 359)
        self.cap_spin.setPrefix("Cap: ")

        btn_apply = QPushButton("Changer de cap")
        btn_apply.clicked.connect(self.change_cap)

        btn_up = QPushButton("Monter (+500m)")
        btn_up.clicked.connect(self.monter)

        btn_down = QPushButton("Descendre (-500m)")
        btn_down.clicked.connect(self.descendre)

        btn_land = QPushButton("Atterrir")
        btn_land.clicked.connect(self.atterrir)

        controls_layout.addWidget(self.cap_spin)
        controls_layout.addWidget(btn_apply)
        controls_layout.addWidget(btn_up)
        controls_layout.addWidget(btn_down)
        controls_layout.addWidget(btn_land)
        controls_group.setLayout(controls_layout)
        right_panel.addWidget(controls_group)
        right_panel.addStretch()

        layout.addLayout(left_panel, 1)
        layout.addWidget(self.radar, 3)
        layout.addLayout(right_panel, 1)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def select_avion_list(self, item):
        name = item.text().split(" ")[0]
        for a in self.avions:
            a.selected = (a.name == name)
            if a.selected:
                self.selected_avion = a
                self.cap_spin.setValue(int(a.cap))

    def change_cap(self):
        if self.selected_avion:
            self.selected_avion.cap = self.cap_spin.value()
            self.selected_avion.is_landing = False

    def monter(self):
        if self.selected_avion:
            self.selected_avion.target_altitude += 500
            self.selected_avion.is_landing = False

    def descendre(self):
        if self.selected_avion:
            self.selected_avion.target_altitude = max(0, self.selected_avion.target_altitude - 500)
            self.selected_avion.is_landing = False

    def atterrir(self):
        if self.selected_avion:
            self.selected_avion.is_landing = True
            self.selected_avion.target_altitude = 0

    def update_sim(self):
        avions_restants = []
        for a in self.avions:
            a.update(0.1)

            if a.is_landing and a.altitude <= 0 and math.hypot(a.x - 300, a.y - 300) < 50:
                self.score += 100
                self.lbl_stats.setText(f"Score: {self.score} - Atterrissage réussi !")
                self.lbl_stats.setStyleSheet("color: #00FF00; font-weight: bold;")
                self.piste_angle = random.randint(0, 359)
                continue

            avions_restants.append(a)

        if len(avions_restants) < len(self.avions):
            self.avions = avions_restants
            if self.selected_avion not in self.avions:
                self.selected_avion = None
            self.list_avions.clear()

        if self.list_avions.count() != len(self.avions):
            self.list_avions.clear()
            for a in self.avions:
                self.list_avions.addItem(
                    f"{a.name} - Alt: {int(a.altitude)}m - V: {a.vitesse}km/h - Fuel: {int(a.fuel)}%")
        else:
            for i, a in enumerate(self.avions):
                self.list_avions.item(i).setText(
                    f"{a.name} - Alt: {int(a.altitude)}m - V: {a.vitesse}km/h - Fuel: {int(a.fuel)}%")
                if a.selected:
                    self.list_avions.item(i).setBackground(QColor(70, 70, 100))
                else:
                    self.list_avions.item(i).setBackground(QColor(30, 30, 30))
                    self.list_avions.item(i).setForeground(QColor(255, 255, 255))

        for i in range(len(self.avions)):
            for j in range(i + 1, len(self.avions)):
                a = self.avions[i]
                b = self.avions[j]
                dist = math.hypot(a.x - b.x, a.y - b.y)
                if dist < 15 and abs(a.altitude - b.altitude) < 500:
                    self.lbl_stats.setText("COLLISION DÉTECTÉE !")
                    self.lbl_stats.setStyleSheet("color: red; font-weight: bold;")

        self.radar.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(palette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(palette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

    window = SimulateurATC()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())