import math
import random

from config.unites import PENTE_APPROCHE, kmh_vers_unites_par_seconde


class Avion:
    """Représente un avion évoluant dans la simulation ATC.

    Unités : altitude en m, vitesse en km/h, cap en °, durées en s
    (voir config/unites.py). Toutes les cadences sont exprimées « par seconde »
    et multipliées par dt : la simulation ne dépend pas de la fréquence de rafraîchissement.
    """

    ALTITUDE_MIN = 0
    ALTITUDE_MIN_DEPART = 2000
    ALTITUDE_MAX_DEPART = 5000

    VITESSE_MIN = 300
    VITESSE_MAX = 500
    VITESSE_APPROCHE = 250.0    # km/h
    ACCELERATION = 20.0         # km/h par seconde

    FUEL_MAX = 100.0
    CONSOMMATION_FUEL = 0.2     # % par seconde
    SEUIL_CARBURANT_FAIBLE = 20.0

    VITESSE_VERTICALE = 25.0             # m/s (montée / descente ordonnée)
    VITESSE_VERTICALE_APPROCHE = 40.0    # m/s (rattrapage de la pente d'approche)
    TAUX_VIRAGE = 5.0                    # °/s

    ALTITUDE_ALERTE = 500
    CORRECTION_MAX_CAP = 45.0
    FORCE_CORRECTION_CAP = 0.4
    TOLERANCE_ALIGNEMENT = 15.0

    # Approche : le point de toucher est situé DISTANCE_POSE unités après le seuil.
    DISTANCE_POSE = 20.0
    ALTITUDE_POSE_MAX = 60.0     # au-dessus de cette hauteur au point de toucher : remise de gaz
    GAIN_REMISE_DE_GAZ = 600     # m

    # Apparition : sur un cercle autour de l'aéroport, cap vers le centre ± ECART_CAP_SPAWN
    MARGE_SPAWN = 50
    ECART_CAP_SPAWN = 25.0

    def __init__(self, name: str, zone_taille: int = 600) -> None:
        self.name = name

        rayon = zone_taille / 2 + self.MARGE_SPAWN
        azimut = random.uniform(0, 360)
        azimut_rad = math.radians(azimut)
        self.x = rayon * math.sin(azimut_rad)
        self.y = -rayon * math.cos(azimut_rad)

        self.altitude = float(random.randint(self.ALTITUDE_MIN_DEPART, self.ALTITUDE_MAX_DEPART))
        self.target_altitude = self.altitude
        self.vitesse_verticale = 0.0  # m/s, utile à l'affichage cockpit

        self.vitesse_croisiere = float(random.randint(self.VITESSE_MIN, self.VITESSE_MAX))
        self.vitesse = self.vitesse_croisiere

        self.cap = float((azimut + 180 + random.uniform(-self.ECART_CAP_SPAWN, self.ECART_CAP_SPAWN)) % 360)
        self.target_cap = self.cap

        self.fuel = self.FUEL_MAX
        self.selected = False
        self._en_alerte = False

        # Navigation & Approche
        self.is_landing = False
        self.is_holding = False
        self.piste_visee = None
        self.sens_approche = 1
        self._evenement: str | None = None

    # ------------------------------------------------------------------ ordres

    def _annuler_manoeuvres(self) -> None:
        """Annule attente / approche en gelant l'altitude actuelle."""
        if self.is_landing:
            self.target_altitude = self.altitude
        self.is_landing = False
        self.is_holding = False
        self.piste_visee = None

    def changer_cap(self, nouveau_cap: float) -> None:
        self._annuler_manoeuvres()
        self.target_cap = float(nouveau_cap % 360)

    def ajuster_cap(self, delta: float) -> None:
        self.changer_cap(self.target_cap + delta)

    def monter(self, delta: int = 500) -> None:
        if delta <= 0:
            return
        self._annuler_manoeuvres()
        self.target_altitude += delta

    def descendre(self, delta: int = 500) -> None:
        if delta <= 0:
            return
        self._annuler_manoeuvres()
        self.target_altitude = max(self.ALTITUDE_MIN, self.target_altitude - delta)

    def demander_atterrissage(self, piste, centre_aeroport: tuple[int, int] = (0, 0)) -> bool:
        """Autorise l'approche sur la piste donnée. Le sens d'approche est figé à cet instant."""
        if piste is None:
            return False
        projection, _ = piste.position_relative(self.x, self.y, centre_aeroport)
        self.sens_approche = piste.sens_approche(projection)
        self.is_landing = True
        self.is_holding = False
        self.piste_visee = piste
        return True

    def effectuer_attente(self) -> None:
        """Active le circuit d'attente (virage continu à 360°)."""
        self._annuler_manoeuvres()
        self.is_holding = True

    def consommer_evenement(self) -> str | None:
        """Retourne (puis efface) le dernier événement notable généré par l'avion."""
        evenement, self._evenement = self._evenement, None
        return evenement

    # ------------------------------------------------------------------ états

    @property
    def en_alerte(self) -> bool:
        # Pas d'alerte « proximité du sol » pour un avion en finale : c'est normal.
        proximite_sol = (
            self.ALTITUDE_MIN < self.altitude <= self.ALTITUDE_ALERTE and not self.is_landing
        )
        return self._en_alerte or proximite_sol

    @en_alerte.setter
    def en_alerte(self, valeur: bool) -> None:
        self._en_alerte = valeur

    @property
    def est_en_vol(self) -> bool:
        return self.altitude > self.ALTITUDE_MIN

    @property
    def carburant_faible(self) -> bool:
        return self.fuel <= self.SEUIL_CARBURANT_FAIBLE

    @property
    def panne_seche(self) -> bool:
        return self.fuel <= 0.0

    # ------------------------------------------------------------------ géométrie piste

    def position_relative_piste(self, centre_aeroport: tuple[int, int]) -> tuple[float, float]:
        """(projection le long de l'axe, écart latéral) par rapport à la piste visée."""
        if self.piste_visee is None:
            return 0.0, 0.0
        return self.piste_visee.position_relative(self.x, self.y, centre_aeroport)

    def distance_au_point_de_pose(self, centre_aeroport: tuple[int, int]) -> float:
        """Distance (unités radar, le long de l'axe) restant à parcourir jusqu'au point de toucher.

        Positive tant que l'avion n'a pas atteint le point de toucher, négative ensuite.
        """
        piste = self.piste_visee
        if piste is None:
            return 0.0
        projection, _ = self.position_relative_piste(centre_aeroport)
        return -piste.longueur / 2 - self.sens_approche * projection + self.DISTANCE_POSE

    def altitude_ideale(self, centre_aeroport: tuple[int, int]) -> float:
        """Altitude (m) sur la pente d'approche à la position actuelle."""
        return max(0.0, self.distance_au_point_de_pose(centre_aeroport)) * PENTE_APPROCHE

    def _cap_vers_piste(self, centre_aeroport: tuple[int, int]) -> float:
        piste = self.piste_visee
        if piste is None:
            return self.target_cap

        _, ecart_lateral = self.position_relative_piste(centre_aeroport)
        sens = self.sens_approche
        cap_piste = piste.cap_atterrissage(sens)

        correction = ecart_lateral * sens * self.FORCE_CORRECTION_CAP
        correction = max(-self.CORRECTION_MAX_CAP, min(self.CORRECTION_MAX_CAP, correction))

        return (cap_piste - correction) % 360

    def sur_piste(self, centre_aeroport: tuple[int, int]) -> bool:
        piste = self.piste_visee
        if piste is None:
            return False

        projection, ecart_lateral = self.position_relative_piste(centre_aeroport)
        return (abs(projection) <= piste.longueur / 2) and (abs(ecart_lateral) <= piste.largeur / 2)

    def est_aligne_piste(self) -> bool:
        """Vérifie que l'écart de cap avec la piste reste acceptable."""
        if self.piste_visee is None:
            return False
        diff1 = abs((self.cap - self.piste_visee.cap + 540) % 360 - 180)
        diff2 = abs((self.cap - self.piste_visee.cap_oppose() + 540) % 360 - 180)
        return min(diff1, diff2) <= self.TOLERANCE_ALIGNEMENT

    def a_atterri(self, centre_aeroport: tuple[int, int]) -> bool:
        """Atterrissage validé : sol touché SUR la piste ET correctement aligné."""
        return (
            self.altitude <= self.ALTITUDE_MIN
            and self.sur_piste(centre_aeroport)
            and self.est_aligne_piste()
        )

    def a_crashe(self, centre_aeroport: tuple[int, int]) -> bool:
        """Crash si le sol est touché hors piste OU désaxé."""
        if self.altitude > self.ALTITUDE_MIN:
            return False
        return not self.sur_piste(centre_aeroport) or not self.est_aligne_piste()

    # ------------------------------------------------------------------ approche

    def _gerer_approche(self, centre_aeroport: tuple[int, int]) -> None:
        """Fait suivre la pente d'approche, ou déclenche une remise de gaz si l'approche est ratée."""
        distance = self.distance_au_point_de_pose(centre_aeroport)

        if distance <= 0:
            trop_haut = self.altitude > self.ALTITUDE_POSE_MAX
            mal_place = not (self.sur_piste(centre_aeroport) and self.est_aligne_piste())
            if trop_haut or mal_place:
                self._remise_de_gaz()
                return

        # Capture de la pente par le dessus uniquement : sous la pente, on garde le palier.
        self.target_altitude = min(self.altitude, self.altitude_ideale(centre_aeroport))

    def _remise_de_gaz(self) -> None:
        self.is_landing = False
        self.piste_visee = None
        self.target_cap = self.cap
        self.target_altitude = self.altitude + self.GAIN_REMISE_DE_GAZ
        self._evenement = f"↻ {self.name} : REMISE DE GAZ"

    # ------------------------------------------------------------------ mise à jour

    def _mettre_a_jour_altitude(self, dt: float) -> None:
        avant = self.altitude
        cadence = self.VITESSE_VERTICALE_APPROCHE if self.is_landing else self.VITESSE_VERTICALE
        difference = self.target_altitude - self.altitude
        pas = min(cadence * dt, abs(difference))
        self.altitude = max(self.ALTITUDE_MIN, self.altitude + math.copysign(pas, difference))
        self.vitesse_verticale = (self.altitude - avant) / dt

    def _mettre_a_jour_vitesse(self, dt: float) -> None:
        cible = self.VITESSE_APPROCHE if self.is_landing else self.vitesse_croisiere
        pas = self.ACCELERATION * dt
        self.vitesse += max(-pas, min(pas, cible - self.vitesse))

    def _mettre_a_jour_cap(self, dt: float) -> None:
        pas = self.TAUX_VIRAGE * dt

        if self.is_holding:
            # Virage continu : le cap avance directement, la consigne le suit.
            self.cap = (self.cap + pas) % 360
            self.target_cap = self.cap
            return

        diff = (self.target_cap - self.cap + 540) % 360 - 180
        if abs(diff) <= pas:
            self.cap = self.target_cap
        else:
            self.cap = (self.cap + (pas if diff > 0 else -pas)) % 360

    def _deplacer(self, dt: float) -> None:
        cap_rad = math.radians(self.cap)
        distance = kmh_vers_unites_par_seconde(self.vitesse) * dt
        self.x += math.sin(cap_rad) * distance
        self.y -= math.cos(cap_rad) * distance

    def _consommer_carburant(self, dt: float) -> None:
        self.fuel = max(0.0, self.fuel - self.CONSOMMATION_FUEL * dt)

    def update(self, dt: float, centre: tuple[int, int] = (0, 0)) -> None:
        if dt <= 0:
            return

        if self.is_landing and self.est_en_vol and self.piste_visee is not None:
            self._gerer_approche(centre)

        self._mettre_a_jour_altitude(dt)
        self._mettre_a_jour_vitesse(dt)

        if self.is_landing and self.est_en_vol and self.piste_visee is not None:
            self.target_cap = self._cap_vers_piste(centre)

        self._mettre_a_jour_cap(dt)
        self._deplacer(dt)
        self._consommer_carburant(dt)
