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

    # --- Instructions ---
    def changer_cap(self, nouveau_cap: int):
        self.cap = nouveau_cap % 360
        self.is_landing = False

    def ajuster_cap(self, delta: int):
        """Utilisé par les flèches du clavier pour un contrôle rapide sans passer par le bouton."""
        self.changer_cap(self.cap + delta)

    def monter(self, delta: int = 500):
        self.target_altitude += delta
        self.is_landing = False

    def descendre(self, delta: int = 500):
        self.target_altitude = max(0, self.target_altitude - delta)
        self.is_landing = False

    def demander_atterrissage(self):
        self.is_landing = True
        self.target_altitude = 0

    # --- Etat ---
    @property
    def en_alerte(self) -> bool:
        """Alarme : l'avion descend sous les 200 m."""
        return 0 < self.altitude <= 200

    # --- Pilotage automatique vers la piste (approche façon ILS) ---
    def _cap_vers_piste(self, piste, centre):
        cx, cy = centre
        cap_rad = math.radians(piste.cap)
        dir_x, dir_y = math.sin(cap_rad), -math.cos(cap_rad)

        rel_x, rel_y = self.x - cx, self.y - cy
        proj = rel_x * dir_x + rel_y * dir_y   # position le long de l'axe de piste
        perp = -rel_x * dir_y + rel_y * dir_x  # écart latéral par rapport à l'axe

        sens = 1 if proj < 0 else -1
        cap_piste = piste.cap if sens == 1 else piste.cap_oppose()

        # correction proportionnelle à l'écart latéral (capture d'axe simplifiée)
        correction = max(-45.0, min(45.0, perp * sens * 0.4))
        return (cap_piste - correction) % 360

    def sur_piste(self, piste, centre) -> bool:
        cx, cy = centre
        cap_rad = math.radians(piste.cap)
        dir_x, dir_y = math.sin(cap_rad), -math.cos(cap_rad)
        rel_x, rel_y = self.x - cx, self.y - cy
        proj = rel_x * dir_x + rel_y * dir_y
        perp = -rel_x * dir_y + rel_y * dir_x

        dans_couloir = abs(proj) <= piste.longueur / 2 and abs(perp) <= piste.largeur / 2
        ecart_cap = min(abs((self.cap - piste.cap) % 360), abs((self.cap - piste.cap_oppose()) % 360))
        return dans_couloir and ecart_cap <= 20

    def a_atterri(self, piste, centre) -> bool:
        return self.is_landing and self.altitude <= 0 and self.sur_piste(piste, centre)

    def a_crashe(self, piste, centre) -> bool:
        return self.altitude <= 0 and not self.sur_piste(piste, centre)

    # --- Simulation ---
    def update(self, dt: float, piste, centre=(300, 300)):
        if self.altitude < self.target_altitude:
            self.altitude += min(20, self.target_altitude - self.altitude)
        elif self.altitude > self.target_altitude:
            self.altitude -= min(20, self.altitude - self.target_altitude)
        self.altitude = max(0, self.altitude)

        if self.is_landing and self.altitude > 0:
            self.cap = self._cap_vers_piste(piste, centre)

        rad = math.radians(self.cap)
        self.x += math.sin(rad) * (self.vitesse / 100) * dt
        self.y -= math.cos(rad) * (self.vitesse / 100) * dt
        self.fuel = max(0.0, self.fuel - 0.1 * dt)