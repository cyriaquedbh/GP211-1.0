import math
import random

from config.airports import Aeroport, Piste
from models.avion import Avion
from models.vent import Vent


class SimulationEngine:
    """Moteur principal de simulation physique et logique ATC."""

    RAYON_SECTEUR = 500          # au-delà : l'avion quitte le secteur (perdu)
    DUREE_EVENEMENT = 5.0        # secondes d'affichage du dernier événement
    POIDS_VENT = 2.0             # unités radar de « bonus » par km/h de vent de face (choix de piste)

    POINTS_ATTERRISSAGE = 100
    PENALITE_PERTE = 150
    PENALITE_SORTIE = 100

    SEUIL_ALERTE = (40, 300)         # (distance horizontale, séparation verticale)
    SEUIL_COLLISION = (15, 150)

    def __init__(self, aeroport: Aeroport, zone_taille: int = 600) -> None:
        self.aeroport = aeroport
        self.zone_taille = zone_taille
        self.avions: list[Avion] = []
        self.score = 0
        self.atterrissages_reussis = 0
        self.crashes = 0
        self.sorties_secteur = 0
        self.vent = Vent()
        self.temps_ecoule = 0.0
        self.prochain_spawn = random.uniform(4, 8)

        self.partie_terminee = False
        self.raison_fin = ""

        self.dernier_evenement = ""
        self.evenement_critique = False
        self._temps_evenement = -math.inf

        # Flotte de départ
        for _ in range(3):
            self.avions.append(Avion(self._nouveau_nom(), zone_taille))

    # ------------------------------------------------------------------ utilitaires

    def centre(self) -> tuple[int, int]:
        """L'origine absolue du monde de la simulation est (0, 0)."""
        return (0, 0)

    def _nouveau_nom(self) -> str:
        noms = {a.name for a in self.avions}
        while True:
            nom = f"AF{random.randint(100, 999)}"
            if nom not in noms:
                return nom

    def _signaler(self, texte: str, critique: bool = False) -> None:
        self.dernier_evenement = texte
        self.evenement_critique = critique
        self._temps_evenement = self.temps_ecoule

    @property
    def evenement_recent(self) -> str:
        """Dernier événement, tant qu'il est récent (vide ensuite)."""
        if self.temps_ecoule - self._temps_evenement <= self.DUREE_EVENEMENT:
            return self.dernier_evenement
        return ""

    def piste_pour_atterrissage(self, avion: Avion) -> Piste:
        """Piste la plus proche, avec préférence pour un atterrissage face au vent."""
        centre = self.centre()

        def cout(piste: Piste) -> float:
            cx, cy = piste.centre(centre)
            projection, _ = piste.position_relative(avion.x, avion.y, centre)
            cap = piste.cap_atterrissage(piste.sens_approche(projection))
            distance = math.hypot(avion.x - cx, avion.y - cy)
            return distance - self.POIDS_VENT * self.vent.composante_face(cap)

        return min(self.aeroport.pistes, key=cout)

    def selectionner(self, avion_cible: Avion | None) -> None:
        for avion in self.avions:
            avion.selected = avion is avion_cible

    # ------------------------------------------------------------------ boucle

    def maj(self, dt: float) -> bool:
        """Avance la simulation de dt secondes. Retourne True si une collision a mis fin à la partie."""
        if self.partie_terminee:
            return True

        self.temps_ecoule += dt
        self.vent.rafraichir()
        self._faire_apparaitre_avions(dt)

        centre = self.centre()
        avions_restants = []

        for avion in self.avions:
            avion.update(dt, centre=centre)

            evenement = avion.consommer_evenement()
            if evenement:
                self._signaler(evenement)

            if avion.a_atterri(centre):
                self.score += self.POINTS_ATTERRISSAGE
                self.atterrissages_reussis += 1
                self._signaler(f"✓ {avion.name} : ATTERRISSAGE CONFIRMÉ")
            elif avion.a_crashe(centre):
                self._perdre(avion, "APPAREIL PERDU")
            elif avion.panne_seche:
                self._perdre(avion, "PANNE SÈCHE")
            elif math.hypot(avion.x - centre[0], avion.y - centre[1]) > self.RAYON_SECTEUR:
                self.score = max(0, self.score - self.PENALITE_SORTIE)
                self.sorties_secteur += 1
                self._signaler(f"⚠ {avion.name} : SORTI DU SECTEUR", critique=True)
            else:
                avions_restants.append(avion)

        self.avions = avions_restants

        collision = self._detecter_collisions()
        if collision:
            self.partie_terminee = True
            self.raison_fin = "COLLISION EN VOL"
            self._signaler("✖ COLLISION EN VOL", critique=True)
        return collision

    def _perdre(self, avion: Avion, motif: str) -> None:
        self.score = max(0, self.score - self.PENALITE_PERTE)
        self.crashes += 1
        self._signaler(f"⚠ {avion.name} : {motif}", critique=True)

    def _faire_apparaitre_avions(self, dt: float) -> None:
        self.prochain_spawn -= dt
        limite_avions = 3 + int(self.temps_ecoule // 25)

        if self.prochain_spawn <= 0 and len(self.avions) < limite_avions:
            self.avions.append(Avion(self._nouveau_nom(), self.zone_taille))
            self.prochain_spawn = random.uniform(6, 12)

    def _detecter_collisions(self) -> bool:
        collision_imminente = False
        for avion in self.avions:
            avion.en_alerte = False

        alerte_h, alerte_v = self.SEUIL_ALERTE
        collision_h, collision_v = self.SEUIL_COLLISION

        for i in range(len(self.avions)):
            for j in range(i + 1, len(self.avions)):
                a, b = self.avions[i], self.avions[j]

                dist_horizontale = math.hypot(a.x - b.x, a.y - b.y)
                dist_verticale = abs(a.altitude - b.altitude)

                if dist_horizontale < alerte_h and dist_verticale < alerte_v:
                    a.en_alerte = True
                    b.en_alerte = True

                if dist_horizontale < collision_h and dist_verticale < collision_v:
                    collision_imminente = True

        return collision_imminente
