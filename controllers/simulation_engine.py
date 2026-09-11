import math
import random

from models.avion import Avion
from models.vent import Vent


class SimulationEngine:
    def __init__(self, aeroport, zone_taille: int = 600):
        self.aeroport = aeroport
        self.zone_taille = zone_taille
        self.avions = []
        self.score = 0
        self.atterrissages_reussis = 0
        self.crashes = 0
        self.piste_active = aeroport.piste_principale()
        self.vent = Vent()
        self.temps_ecoule = 0.0
        self.prochain_spawn = random.uniform(5, 10)
        self.dernier_evenement = ""

        for i in range(3):
            self.avions.append(Avion(f"AF10{i}", zone_taille))

    def centre(self):
        return (self.zone_taille // 2, self.zone_taille // 2)

    def maj(self, dt: float) -> bool:
        self.temps_ecoule += dt
        self.vent.rafraichir()
        self._faire_apparaitre_avions(dt)

        avions_restants = []
        for avion in self.avions:
            avion.update(dt, self.piste_active, centre=self.centre())

            if avion.a_atterri(self.piste_active, self.centre()):
                self.score += 100
                self.atterrissages_reussis += 1
                self.dernier_evenement = f"{avion.name} a atterri avec succès !"
                self.piste_active = random.choice(self.aeroport.pistes)
                continue

            if avion.a_crashe(self.piste_active, self.centre()):
                self.score = max(0, self.score - 150)
                self.crashes += 1
                self.dernier_evenement = f"{avion.name} s'est crashé !"
                continue

            avions_restants.append(avion)
        self.avions = avions_restants

        return self._detecter_collisions()

    def _faire_apparaitre_avions(self, dt):
        self.prochain_spawn -= dt
        limite = 3 + int(self.temps_ecoule // 30)
        if self.prochain_spawn <= 0 and len(self.avions) < limite:
            self.avions.append(Avion(f"AF{random.randint(100, 999)}", self.zone_taille))
            self.prochain_spawn = random.uniform(5, 10)

    def _detecter_collisions(self):
        for i in range(len(self.avions)):
            for j in range(i + 1, len(self.avions)):
                a, b = self.avions[i], self.avions[j]
                if math.hypot(a.x - b.x, a.y - b.y) < 15 and abs(a.altitude - b.altitude) < 500:
                    return True
        return False

    def selectionner(self, avion):
        for a in self.avions:
            a.selected = (a is avion)