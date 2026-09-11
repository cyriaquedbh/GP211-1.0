import random


class Vent:
    """Modèle de vent aéronautique (direction d'origine et vitesse)."""

    def __init__(self):
        self.direction = random.randint(0, 359)
        self.vitesse = random.randint(5, 25)

    def rafraichir(self, proba_changement: float = 0.002) -> None:
        """Applique une variation stochastique progressive à la direction et la vitesse."""
        if random.random() < proba_changement:
            delta_direction = random.randint(-15, 15)
            self.direction = (self.direction + delta_direction) % 360

            delta_vitesse = random.randint(-2, 2)
            self.vitesse = max(0, min(60, self.vitesse + delta_vitesse))

    @property
    def vitesse_noeuds(self) -> int:
        """Retourne la vitesse convertie en nœuds (kts)."""
        return int(self.vitesse / 1.852)

    def __str__(self) -> str:
        return f"{self.direction:03d}° / {self.vitesse} km/h"

    def __repr__(self) -> str:
        return self.__str__()