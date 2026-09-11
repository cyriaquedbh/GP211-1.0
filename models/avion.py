import math
import random


class Avion:
    def __init__(self, name: str, zone_taille: int = 600):
        self.name = name
        self.x = random.uniform(50, zone_taille - 50)
        self.y = random.uniform(50, zone_taille - 50)
        self.altitude = random.randint(2000, 5000)
        self.target_altitude = self.altitude
        self.vitesse = random.randint(300, 500)
        self.cap = random.randint(0, 359)
        self.fuel = 100.0
        self.selected = False
        self.is_landing = False
        self.piste_visee = None  # Piste assignée pour l'atterrissage en cours

    # --- Instructions ---
    def changer_cap(self, nouveau_cap: int):
        self.cap = nouveau_cap % 360

    def ajuster_cap(self, delta: int):
        self.changer_cap(self.cap + delta)

    def monter(self, delta: int = 500):
        self.target_altitude += delta
        self.is_landing = False

    def descendre(self, delta: int = 500):
        self.target_altitude = max(0, self.target_altitude - delta)
        self.is_landing = False

    def demander_atterrissage(self, piste):
        self.is_landing = True
        self.piste_visee = piste
        self.target_altitude = 0

    # --- Etat ---
    @property
    def en_alerte(self) -> bool:
        return 0 < self.altitude <= 500

    # --- Pilotage automatique vers la piste visée (approche façon ILS) ---
    def _cap_vers_piste(self, centre_aeroport):
        piste = self.piste_visee
        cx, cy = piste.centre(centre_aeroport)
        cap_rad = math.radians(piste.cap)
        dir_x, dir_y = math.sin(cap_rad), -math.cos(cap_rad)

        rel_x, rel_y = self.x - cx, self.y - cy
        proj = rel_x * dir_x + rel_y * dir_y
        perp = -rel_x * dir_y + rel_y * dir_x

        sens = 1 if proj < 0 else -1
        cap_piste = piste.cap if sens == 1 else piste.cap_oppose()

        correction = max(-45.0, min(45.0, perp * sens * 0.4))
        return (cap_piste - correction) % 360

    def sur_piste(self, centre_aeroport) -> bool:
        """True si l'avion est dans le rectangle (longueur x largeur) de la piste visée."""
        piste = self.piste_visee
        if piste is None:
            return False
        cx, cy = piste.centre(centre_aeroport)
        cap_rad = math.radians(piste.cap)
        dir_x, dir_y = math.sin(cap_rad), -math.cos(cap_rad)
        rel_x, rel_y = self.x - cx, self.y - cy
        proj = rel_x * dir_x + rel_y * dir_y
        perp = -rel_x * dir_y + rel_y * dir_x
        return abs(proj) <= piste.longueur / 2 and abs(perp) <= piste.largeur / 2

    def a_atterri(self, centre_aeroport) -> bool:
        return self.altitude <= 0 and self.sur_piste(centre_aeroport)

    def a_crashe(self, centre_aeroport) -> bool:
        return self.altitude <= 0 and not self.sur_piste(centre_aeroport)

    # --- Simulation ---
    def update(self, dt: float, centre: tuple = (300, 300)):
        if self.altitude < self.target_altitude:
            self.altitude += min(20, self.target_altitude - self.altitude)
        elif self.altitude > self.target_altitude:
            self.altitude -= min(20, self.altitude - self.target_altitude)
        self.altitude = max(0, self.altitude)

        if self.is_landing and self.altitude > 0 and self.piste_visee is not None:
            self.cap = self._cap_vers_piste(centre)

        rad = math.radians(self.cap)
        self.x += math.sin(rad) * (self.vitesse / 100) * dt
        self.y -= math.cos(rad) * (self.vitesse / 100) * dt
        self.fuel = max(0.0, self.fuel - 0.1 * dt)