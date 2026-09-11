import random


class Vent:
    """Vent simplifié : direction d'où il souffle (convention aéronautique) + vitesse."""

    def __init__(self):
        self.direction = random.randint(0, 359)
        self.vitesse = random.randint(5, 25)

    def rafraichir(self, proba_changement: float = 0.002):
        if random.random() < proba_changement:
            self.direction = (self.direction + random.randint(-15, 15)) % 360
            self.vitesse = max(0, min(60, self.vitesse + random.randint(-2, 2)))

    def __str__(self):
        return f"{self.direction:03d}° / {self.vitesse} km/h"