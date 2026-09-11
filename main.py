import sys
from PySide6.QtWidgets import QApplication

from utils.theme import appliquer_theme_sombre
from ui.menu_selection import MenuSelectionAeroport
from ui.main_window import SimulateurATC


def main():
    app = QApplication(sys.argv)
    appliquer_theme_sombre(app)

    menu = MenuSelectionAeroport()
    if menu.exec() == MenuSelectionAeroport.Accepted:
        aeroport = menu.get_aeroport_selectionne()
        fenetre = SimulateurATC(aeroport)
        fenetre.resize(1000, 600)
        fenetre.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()