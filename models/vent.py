import math
import random


class Vent:
    """Modèle de vent aéronautique : direction d'ORIGINE (°) et vitesse (km/h)."""

    VITESSE_MAX = 60

    def __init__(self) -> None:
        self.direction = random.randint(0, 359)
        self.vitesse = random.randint(5, 25)

    def rafraichir(self, proba_changement: float = 0.002) -> None:
        """Applique une variation stochastique progressive à la direction et la vitesse."""
        if random.random() < proba_changement:
            delta_direction = random.randint(-15, 15)
            self.direction = (self.direction + delta_direction) % 360

            delta_vitesse = random.randint(-2, 2)
            self.vitesse = max(0, min(self.VITESSE_MAX, self.vitesse + delta_vitesse))

    def composante_face(self, cap: float) -> float:
        """Vent de face (> 0) ou arrière (< 0), en km/h, pour un avion roulant au cap donné."""
        return self.vitesse * math.cos(math.radians(cap - self.direction))

    def __str__(self) -> str:
        return f"{self.direction:03d}° / {self.vitesse} km/h"

    def __repr__(self) -> str:
        return self.__str__()
