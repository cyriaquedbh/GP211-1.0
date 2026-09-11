import math
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainterPath, QPen, QColor


def piste_la_plus_proche(avion, pistes, centre):
    """Retourne, parmi une liste de pistes, celle dont l'axe est le plus proche de l'avion."""
    meilleure, meilleure_dist = None, float("inf")
    for piste in pistes:
        cx, cy = piste.centre(centre)
        dist = math.hypot(avion.x - cx, avion.y - cy)
        if dist < meilleure_dist:
            meilleure, meilleure_dist = piste, dist
    return meilleure


def dessiner_trajectoire(painter, avion, piste, centre):
    """
    Dessine, en pâle et transparent, le chemin que l'avion sélectionné doit
    suivre pour rejoindre l'axe de la piste puis se poser sur toute sa longueur.
    """
    if piste is None:
        return

    cx, cy = piste.centre(centre)
    cap_rad = math.radians(piste.cap)
    dir_x, dir_y = math.sin(cap_rad), -math.cos(cap_rad)

    rel_x, rel_y = avion.x - cx, avion.y - cy
    proj = rel_x * dir_x + rel_y * dir_y
    sens = 1 if proj < 0 else -1  # côté d'où arrive l'avion

    demi_longueur = piste.longueur / 2
    seuil = QPointF(cx - sens * dir_x * demi_longueur, cy - sens * dir_y * demi_longueur)
    fin_piste = QPointF(cx + sens * dir_x * demi_longueur, cy + sens * dir_y * demi_longueur)
    point_interception = QPointF(
        cx - sens * dir_x * (demi_longueur + 60),
        cy - sens * dir_y * (demi_longueur + 60),
    )

    # Surbrillance pâle de toute la piste (atterrissage possible sur toute sa longueur)
    painter.save()
    painter.translate(cx, cy)
    painter.rotate(piste.cap)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(255, 255, 255, 25))
    painter.drawRect(int(-piste.largeur / 2), int(-piste.longueur / 2), piste.largeur, piste.longueur)
    painter.restore()

    # Trajectoire pâle et transparente : avion -> seuil -> bout de piste
    chemin = QPainterPath(QPointF(avion.x, avion.y))
    chemin.quadTo(point_interception, seuil)
    chemin.lineTo(fin_piste)

    painter.save()
    painter.setPen(QPen(QColor(255, 255, 255, 130), 2, Qt.DashLine))
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(chemin)
    painter.restore()