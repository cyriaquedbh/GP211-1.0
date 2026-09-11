import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPen


def piste_la_plus_proche(avion, pistes, centre):
    """Retourne la piste la plus proche de l'appareil sélectionné."""
    meilleure, meilleure_dist = None, float("inf")
    for piste in pistes:
        cx, cy = piste.centre(centre)
        dist = math.hypot(avion.x - cx, avion.y - cy)
        if dist < meilleure_dist:
            meilleure, meilleure_dist = piste, dist
    return meilleure


def dessiner_trajectoire(painter, avion, piste, centre):
    """Dessine la trajectoire prédictive d'approche et d'alignement ILS."""
    if piste is None:
        return

    cx, cy = piste.centre(centre)
    cap_rad = math.radians(piste.cap)
    dir_x, dir_y = math.sin(cap_rad), -math.cos(cap_rad)

    rel_x, rel_y = avion.x - cx, avion.y - cy
    proj = rel_x * dir_x + rel_y * dir_y
    sens = 1 if proj < 0 else -1

    demi_longueur = piste.longueur / 2
    seuil = QPointF(
        cx - sens * dir_x * demi_longueur,
        cy - sens * dir_y * demi_longueur,
    )
    fin_piste = QPointF(
        cx + sens * dir_x * demi_longueur,
        cy + sens * dir_y * demi_longueur,
    )

    # Point de capture de l'axe de descente (Glide Path)
    point_interception = QPointF(
        cx - sens * dir_x * (demi_longueur + 80),
        cy - sens * dir_y * (demi_longueur + 80),
    )

    painter.save()

    # 1. Surbrillance néon de la piste visée
    painter.translate(cx, cy)
    painter.rotate(piste.cap)
    painter.setPen(QPen(QColor(56, 189, 248, 120), 1.5))
    painter.setBrush(QColor(56, 189, 248, 25))
    painter.drawRoundedRect(
        -piste.largeur / 2,
        -piste.longueur / 2,
        piste.largeur,
        piste.longueur,
        2,
        2,
    )
    painter.restore()

    # 2. Vecteur d'approche ILS (Courbe de Bézier)
    chemin = QPainterPath(QPointF(avion.x, avion.y))
    chemin.quadTo(point_interception, seuil)
    chemin.lineTo(fin_piste)

    # Ombre de contraste pour le tracé
    painter.save()
    painter.setPen(QPen(QColor(4, 8, 14, 220), 4, Qt.SolidLine))
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(chemin)

    # Ligne d'approche pointillée Cyan/Cyan Néon
    painter.setPen(QPen(QColor(56, 189, 248, 200), 2, Qt.DashLine))
    painter.drawPath(chemin)

    # Balise visuelle sur le seuil de piste (Touchdown Zone)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(251, 191, 36, 220))
    painter.drawEllipse(seuil, 4, 4)

    painter.restore()