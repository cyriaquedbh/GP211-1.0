from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPen


def dessiner_trajectoire(painter, avion, piste, centre) -> None:
    """Dessine la trajectoire prédictive d'approche et d'alignement ILS."""
    if piste is None:
        return

    cx, cy = piste.centre(centre)
    dir_x, dir_y = piste.direction()

    # Sens figé si l'avion est déjà autorisé sur cette piste, sinon déduit de sa position.
    if avion.is_landing and avion.piste_visee is piste:
        sens = avion.sens_approche
    else:
        projection, _ = piste.position_relative(avion.x, avion.y, centre)
        sens = piste.sens_approche(projection)

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

    # 2. Vecteur d'approche ILS (courbe de Bézier)
    chemin = QPainterPath(QPointF(avion.x, avion.y))
    chemin.quadTo(point_interception, seuil)
    chemin.lineTo(fin_piste)

    # Ombre de contraste pour le tracé
    painter.save()
    painter.setPen(QPen(QColor(4, 8, 14, 220), 4, Qt.SolidLine))
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(chemin)

    # Ligne d'approche pointillée cyan
    painter.setPen(QPen(QColor(56, 189, 248, 200), 2, Qt.DashLine))
    painter.drawPath(chemin)

    # Balise visuelle sur le seuil de piste (zone de toucher)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(251, 191, 36, 220))
    painter.drawEllipse(seuil, 4, 4)

    painter.restore()
