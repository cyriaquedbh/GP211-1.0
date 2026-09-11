import math
import random


class Avion:
    """Représente un avion évoluant dans la simulation ATC."""

    ALTITUDE_MIN = 0
    ALTITUDE_MIN_DEPART = 2000
    ALTITUDE_MAX_DEPART = 5000

    VITESSE_MIN = 300
    VITESSE_MAX = 500

    FUEL_MAX = 100.0
    CONSOMMATION_FUEL = 0.1

    VITESSE_MONTEE_PAR_TICK = 20
    TAUX_VIRAGE = 1.5

    ALTITUDE_ALERTE = 500
    CORRECTION_MAX_CAP = 45.0
    FORCE_CORRECTION_CAP = 0.4

    def __init__(self, name: str, zone_taille: int = 600):
        self.name = name

        # Position initiale générée autour de l'origine (0, 0)
        rayon_max = zone_taille // 2 - 50
        self.x = random.uniform(-rayon_max, rayon_max)
        self.y = random.uniform(-rayon_max, rayon_max)

        self.altitude = random.randint(self.ALTITUDE_MIN_DEPART, self.ALTITUDE_MAX_DEPART)
        self.target_altitude = self.altitude

        self.vitesse = random.randint(self.VITESSE_MIN, self.VITESSE_MAX)

        self.cap = float(random.randint(0, 359))
        self.target_cap = self.cap

        self.fuel = self.FUEL_MAX
        self.selected = False
        self._en_alerte = False

        self.is_landing = False
        self.piste_visee = None

    def changer_cap(self, nouveau_cap: int):
        self.target_cap = float(nouveau_cap % 360)

    def ajuster_cap(self, delta: int):
        self.changer_cap(self.target_cap + delta)

    def monter(self, delta: int = 500):
        if delta <= 0:
            return
        self.target_altitude += delta
        self.is_landing = False
        self.piste_visee = None

    def descendre(self, delta: int = 500):
        if delta <= 0:
            return
        self.target_altitude = max(self.ALTITUDE_MIN, self.target_altitude - delta)
        self.is_landing = False
        self.piste_visee = None

    def demander_atterrissage(self, piste):
        if piste is None:
            return
        self.is_landing = True
        self.piste_visee = piste
        self.target_altitude = self.ALTITUDE_MIN

    @property
    def en_alerte(self) -> bool:
        proximite_sol = (self.ALTITUDE_MIN < self.altitude <= self.ALTITUDE_ALERTE)
        return self._en_alerte or proximite_sol

    @en_alerte.setter
    def en_alerte(self, valeur: bool):
        self._en_alerte = valeur

    @property
    def est_en_vol(self) -> bool:
        return self.altitude > self.ALTITUDE_MIN

    @property
    def carburant_faible(self) -> bool:
        return self.fuel <= 20.0

    def _direction_piste(self, piste):
        cap_rad = math.radians(piste.cap)
        return math.sin(cap_rad), -math.cos(cap_rad)

    def _position_relative_piste(self, centre_aeroport):
        piste = self.piste_visee
        if piste is None:
            return 0.0, 0.0

        centre_x, centre_y = piste.centre(centre_aeroport)
        direction_x, direction_y = self._direction_piste(piste)

        relative_x = self.x - centre_x
        relative_y = self.y - centre_y

        projection = relative_x * direction_x + relative_y * direction_y
        ecart_lateral = -relative_x * direction_y + relative_y * direction_x

        return projection, ecart_lateral

    def _cap_vers_piste(self, centre_aeroport):
        piste = self.piste_visee
        if piste is None:
            return self.target_cap

        projection, ecart_lateral = self._position_relative_piste(centre_aeroport)

        if projection < 0:
            sens = 1
            cap_piste = piste.cap
        else:
            sens = -1
            cap_piste = piste.cap_oppose()

        correction = ecart_lateral * sens * self.FORCE_CORRECTION_CAP
        correction = max(-self.CORRECTION_MAX_CAP, min(self.CORRECTION_MAX_CAP, correction))

        return (cap_piste - correction) % 360

    def sur_piste(self, centre_aeroport) -> bool:
        piste = self.piste_visee
        if piste is None:
            return False

        projection, ecart_lateral = self._position_relative_piste(centre_aeroport)
        return (abs(projection) <= piste.longueur / 2) and (abs(ecart_lateral) <= piste.largeur / 2)

    def a_atterri(self, centre_aeroport) -> bool:
        return self.altitude <= self.ALTITUDE_MIN and self.sur_piste(centre_aeroport)

    def a_crashe(self, centre_aeroport) -> bool:
        return self.altitude <= self.ALTITUDE_MIN and not self.sur_piste(centre_aeroport)

    def _mettre_a_jour_altitude(self):
        difference = self.target_altitude - self.altitude
        if difference > 0:
            self.altitude += min(self.VITESSE_MONTEE_PAR_TICK, difference)
        elif difference < 0:
            self.altitude -= min(self.VITESSE_MONTEE_PAR_TICK, abs(difference))
        self.altitude = max(self.ALTITUDE_MIN, self.altitude)

    def _mettre_a_jour_cap(self):
        diff = (self.target_cap - self.cap + 540) % 360 - 180
        if abs(diff) <= self.TAUX_VIRAGE:
            self.cap = self.target_cap
        else:
            self.cap = (self.cap + (self.TAUX_VIRAGE if diff > 0 else -self.TAUX_VIRAGE)) % 360

    def _deplacer(self, dt: float):
        if dt <= 0:
            return
        cap_rad = math.radians(self.cap)
        distance = (self.vitesse / 100) * dt
        self.x += math.sin(cap_rad) * distance
        self.y -= math.cos(cap_rad) * distance

    def _consommer_carburant(self, dt: float):
        if dt <= 0:
            return
        self.fuel = max(0.0, self.fuel - self.CONSOMMATION_FUEL * dt)

    def update(self, dt: float, centre: tuple[int, int] = (0, 0)):
        if dt <= 0:
            return

        self._mettre_a_jour_altitude()

        if self.is_landing and self.est_en_vol and self.piste_visee is not None:
            self.target_cap = self._cap_vers_piste(centre)

        self._mettre_a_jour_cap()
        self._deplacer(dt)
        self._consommer_carburant(dt)