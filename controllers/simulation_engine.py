import math
import random

from models.avion import Avion
from models.vent import Vent


class SimulationEngine:
    """Moteur principal de simulation physique et logique ATC."""

    def __init__(self, aeroport, zone_taille: int = 600):
        self.aeroport = aeroport
        self.zone_taille = zone_taille
        self.avions = []
        self.score = 0
        self.atterrissages_reussis = 0
        self.crashes = 0
        self.vent = Vent()
        self.temps_ecoule = 0.0
        self.prochain_spawn = random.uniform(4, 8)
        self.dernier_evenement = ""

        # Initialisation avec la flotte de départ autour de l'origine
        for i in range(3):
            self.avions.append(
                Avion(f"AF{random.randint(100, 400)}", zone_taille)
            )

    def centre(self) -> tuple[int, int]:
        """L'origine absolue du monde de la simulation est (0, 0)."""
        return (0, 0)

    def piste_la_plus_proche(self, avion):
        """Assigne la piste la plus proche de l'appareil sélectionné."""
        centre = self.centre()
        return min(
            self.aeroport.pistes,
            key=lambda p: math.hypot(
                avion.x - p.centre(centre)[0], avion.y - p.centre(centre)[1]
            ),
        )

    def maj(self, dt: float) -> bool:
        self.temps_ecoule += dt
        self.vent.rafraichir()
        self._faire_apparaitre_avions(dt)

        centre = self.centre()
        avions_restants = []

        for avion in self.avions:
            avion.update(dt, centre=centre)

            if avion.a_atterri(centre):
                self.score += 100
                self.atterrissages_reussis += 1
                self.dernier_evenement = f"✓ {avion.name} : ATTERRISSAGE CONFIRMÉ"
                continue

            if avion.a_crashe(centre):
                self.score = max(0, self.score - 150)
                self.crashes += 1
                self.dernier_evenement = f"⚠ {avion.name} : APPAREIL PERDU"
                continue

            avions_restants.append(avion)

        self.avions = avions_restants
        return self._detecter_collisions()

    def _faire_apparaitre_avions(self, dt: float):
        self.prochain_spawn -= dt
        limite_avions = 3 + int(self.temps_ecoule // 25)

        if self.prochain_spawn <= 0 and len(self.avions) < limite_avions:
            nouveau_vol = f"AF{random.randint(100, 999)}"
            self.avions.append(Avion(nouveau_vol, self.zone_taille))
            self.prochain_spawn = random.uniform(6, 12)

    def _detecter_collisions(self) -> bool:
        collision_imminente = False
        for avion in self.avions:
            avion.en_alerte = False

        for i in range(len(self.avions)):
            for j in range(i + 1, len(self.avions)):
                a, b = self.avions[i], self.avions[j]

                dist_horizontale = math.hypot(a.x - b.x, a.y - b.y)
                dist_verticale = abs(a.altitude - b.altitude)

                if dist_horizontale < 40 and dist_verticale < 300:
                    a.en_alerte = True
                    b.en_alerte = True

                if dist_horizontale < 15 and dist_verticale < 150:
                    collision_imminente = True

        return collision_imminente

    def selectionner(self, avion_cible):
        for avion in self.avions:
            avion.selected = avion is avion_cible