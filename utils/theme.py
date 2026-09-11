from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette


def appliquer_theme_sombre(app):
    app.setStyle("Fusion")

    palette = QPalette()

    # Couleurs de base des fenêtres et contenus
    palette.setColor(QPalette.ColorRole.Window, QColor(15, 23, 42))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(241, 245, 249))
    palette.setColor(QPalette.ColorRole.Base, QColor(11, 15, 23))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(22, 31, 48))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 41, 59))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(241, 245, 249))
    palette.setColor(QPalette.ColorRole.Text, QColor(241, 245, 249))

    # Boutons et commandes
    palette.setColor(QPalette.ColorRole.Button, QColor(22, 31, 48))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(241, 245, 249))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(239, 68, 68))

    # Mises en surbrillance (Sélections, focus)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(56, 189, 248))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(15, 23, 42))

    # Élément désactivés (Disabled)
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(100, 116, 139),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(100, 116, 139),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(100, 116, 139),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Highlight,
        QColor(51, 65, 85),
    )

    app.setPalette(palette)