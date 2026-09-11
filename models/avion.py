import math
import random


class Avion:
    """Représente un avion évoluant dans la simulation ATC."""

    # ------------------------------------------------------------
    # Paramètres de simulation
    # ------------------------------------------------------------

    ALTITUDE_MIN = 0
    ALTITUDE_MIN_DEPART = 2000
    ALTITUDE_MAX_DEPART = 5000

    VITESSE_MIN = 300
    VITESSE_MAX = 500

    FUEL_MAX = 100.0
    CONSOMMATION_FUEL = 0.1

    VITESSE_MONTEE_PAR_TICK = 20

    DISTANCE_MIN_BORD = 50

    ALTITUDE_ALERTE = 500

    CORRECTION_MAX_CAP = 45.0
    FORCE_CORRECTION_CAP = 0.4

    # ------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------

    def __init__(self, name: str, zone_taille: int = 600):
        self.name = name

        # Position initiale
        marge = self.DISTANCE_MIN_BORD

        self.x = random.uniform(
            marge,
            zone_taille - marge
        )

        self.y = random.uniform(
            marge,
            zone_taille - marge
        )

        # Altitude
        self.altitude = random.randint(
            self.ALTITUDE_MIN_DEPART,
            self.ALTITUDE_MAX_DEPART
        )

        self.target_altitude = self.altitude

        # Vitesse et cap
        self.vitesse = random.randint(
            self.VITESSE_MIN,
            self.VITESSE_MAX
        )

        self.cap = random.randint(0, 359)

        # État
        self.fuel = self.FUEL_MAX
        self.selected = False

        # Atterrissage
        self.is_landing = False
        self.piste_visee = None

    # ============================================================
    # INSTRUCTIONS
    # ============================================================

    def changer_cap(self, nouveau_cap: int):
        """Définit un nouveau cap compris entre 0° et 359°."""
        self.cap = nouveau_cap % 360

    def ajuster_cap(self, delta: int):
        """Modifie le cap actuel d'un certain nombre de degrés."""
        self.changer_cap(self.cap + delta)

    def monter(self, delta: int = 500):
        """Demande à l'avion de monter."""
        if delta <= 0:
            return

        self.target_altitude += delta
        self.is_landing = False
        self.piste_visee = None

    def descendre(self, delta: int = 500):
        """Demande à l'avion de descendre."""
        if delta <= 0:
            return

        self.target_altitude = max(
            self.ALTITUDE_MIN,
            self.target_altitude - delta
        )

        self.is_landing = False
        self.piste_visee = None

    def demander_atterrissage(self, piste):
        """Demande un atterrissage sur une piste donnée."""
        if piste is None:
            return

        self.is_landing = True
        self.piste_visee = piste
        self.target_altitude = self.ALTITUDE_MIN

    # ============================================================
    # ÉTAT DE L'AVION
    # ============================================================

    @property
    def en_alerte(self) -> bool:
        """Indique si l'avion vole dangereusement près du sol."""
        return (
            self.ALTITUDE_MIN
            < self.altitude
            <= self.ALTITUDE_ALERTE
        )

    @property
    def est_en_vol(self) -> bool:
        """Indique si l'avion est encore en l'air."""
        return self.altitude > self.ALTITUDE_MIN

    @property
    def carburant_faible(self) -> bool:
        """Indique si le niveau de carburant est faible."""
        return self.fuel <= 20.0

    # ============================================================
    # CALCULS DE NAVIGATION
    # ============================================================

    def _direction_piste(self, piste):
        """
        Retourne le vecteur unitaire correspondant à l'axe
        de la piste.
        """
        cap_rad = math.radians(piste.cap)

        direction_x = math.sin(cap_rad)
        direction_y = -math.cos(cap_rad)

        return direction_x, direction_y

    def _position_relative_piste(self, centre_aeroport):
        """
        Calcule la position de l'avion relativement au centre
        de sa piste.

        Retourne :
            projection : position le long de la piste
            ecart_lateral : distance perpendiculaire à la piste
        """
        piste = self.piste_visee

        if piste is None:
            return 0.0, 0.0

        centre_x, centre_y = piste.centre(centre_aeroport)

        direction_x, direction_y = self._direction_piste(piste)

        relative_x = self.x - centre_x
        relative_y = self.y - centre_y

        projection = (
            relative_x * direction_x
            + relative_y * direction_y
        )

        ecart_lateral = (
            -relative_x * direction_y
            + relative_y * direction_x
        )

        return projection, ecart_lateral

    def _cap_vers_piste(self, centre_aeroport):
        """
        Calcule automatiquement le cap nécessaire pour rejoindre
        la piste visée.

        Le comportement simule une approche simplifiée de type ILS.
        """
        piste = self.piste_visee

        if piste is None:
            return self.cap

        projection, ecart_lateral = (
            self._position_relative_piste(centre_aeroport)
        )

        # Choix du sens d'approche
        if projection < 0:
            sens = 1
            cap_piste = piste.cap
        else:
            sens = -1
            cap_piste = piste.cap_oppose()

        # Correction latérale limitée
        correction = ecart_lateral * sens * self.FORCE_CORRECTION_CAP

        correction = max(
            -self.CORRECTION_MAX_CAP,
            min(self.CORRECTION_MAX_CAP, correction)
        )

        return (cap_piste - correction) % 360

    # ============================================================
    # POSITION SUR LA PISTE
    # ============================================================

    def sur_piste(self, centre_aeroport) -> bool:
        """
        Vérifie si l'avion se trouve à l'intérieur du rectangle
        représentant la piste visée.
        """
        piste = self.piste_visee

        if piste is None:
            return False

        projection, ecart_lateral = (
            self._position_relative_piste(centre_aeroport)
        )

        dans_la_longueur = (
            abs(projection)
            <= piste.longueur / 2
        )

        dans_la_largeur = (
            abs(ecart_lateral)
            <= piste.largeur / 2
        )

        return dans_la_longueur and dans_la_largeur

    def a_atterri(self, centre_aeroport) -> bool:
        """Indique si l'avion a correctement atterri."""
        return (
            self.altitude <= self.ALTITUDE_MIN
            and self.sur_piste(centre_aeroport)
        )

    def a_crashe(self, centre_aeroport) -> bool:
        """Indique si l'avion a atteint le sol hors de la piste."""
        return (
            self.altitude <= self.ALTITUDE_MIN
            and not self.sur_piste(centre_aeroport)
        )

    # ============================================================
    # GESTION DE L'ALTITUDE
    # ============================================================

    def _mettre_a_jour_altitude(self):
        """Fait progressivement évoluer l'altitude vers la cible."""

        difference = (
            self.target_altitude
            - self.altitude
        )

        if difference > 0:
            self.altitude += min(
                self.VITESSE_MONTEE_PAR_TICK,
                difference
            )

        elif difference < 0:
            self.altitude -= min(
                self.VITESSE_MONTEE_PAR_TICK,
                abs(difference)
            )

        self.altitude = max(
            self.ALTITUDE_MIN,
            self.altitude
        )

    # ============================================================
    # DÉPLACEMENT
    # ============================================================

    def _deplacer(self, dt: float):
        """Déplace l'avion en fonction de son cap et de sa vitesse."""

        if dt <= 0:
            return

        cap_rad = math.radians(self.cap)

        distance = (
            self.vitesse / 100
        ) * dt

        self.x += math.sin(cap_rad) * distance
        self.y -= math.cos(cap_rad) * distance

    # ============================================================
    # CARBURANT
    # ============================================================

    def _consommer_carburant(self, dt: float):
        """Diminue progressivement le niveau de carburant."""

        if dt <= 0:
            return

        consommation = (
            self.CONSOMMATION_FUEL * dt
        )

        self.fuel = max(
            0.0,
            self.fuel - consommation
        )

    # ============================================================
    # SIMULATION
    # ============================================================

    def update(
        self,
        dt: float,
        centre: tuple[int, int] = (300, 300)
    ):
        """
        Met à jour l'état de l'avion pour un cycle de simulation.

        Args:
            dt:
                Durée du cycle de simulation.

            centre:
                Coordonnées du centre de l'aéroport.
        """

        if dt <= 0:
            return

        # 1. Mise à jour de l'altitude
        self._mettre_a_jour_altitude()

        # 2. Navigation automatique pendant l'approche
        if (
            self.is_landing
            and self.est_en_vol
            and self.piste_visee is not None
        ):
            self.cap = self._cap_vers_piste(centre)

        # 3. Déplacement
        self._deplacer(dt)

        # 4. Consommation de carburant
        self._consommer_carburant(dt)