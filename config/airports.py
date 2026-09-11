from dataclasses import dataclass, field


# ============================================================
# CONFIGURATION DE LA CARTE
# ============================================================

# 1 unité de la carte = 20 mètres réels
ECHELLE_METRES_PAR_UNITE = 20

# Taille de la carte jouable
TAILLE_CARTE = 1200


def m_vers_radar(longueur_m: int) -> int:
    """Convertit une distance réelle en unités de carte."""
    return round(longueur_m / ECHELLE_METRES_PAR_UNITE)


# ============================================================
# PISTES
# ============================================================

@dataclass
class Piste:
    """Représente une piste d'aéroport."""

    nom: str
    cap: int
    longueur: int
    largeur: int = 34

    decalage_x: int = 0
    decalage_y: int = 0

    def cap_oppose(self) -> int:
        """Retourne le cap de l'autre extrémité de la piste."""
        return (self.cap + 180) % 360

    def centre(self, centre_aeroport: tuple[int, int]) -> tuple[int, int]:
        """Retourne le centre de la piste sur la carte."""
        return (
            centre_aeroport[0] + self.decalage_x,
            centre_aeroport[1] + self.decalage_y,
        )


# ============================================================
# TERMINAUX
# ============================================================

@dataclass
class Terminal:
    """
    Représente un terminal sur la carte.

    x/y sont les coordonnées du centre du terminal.
    largeur/hauteur sont exprimées en unités de carte.
    """

    nom: str

    x: int
    y: int

    largeur: int
    hauteur: int

    rotation: float = 0.0

    # Couleur logique du bâtiment.
    # Le RadarWidget pourra ensuite lui attribuer son propre style.
    type_batiment: str = "terminal"

    def centre(self) -> tuple[int, int]:
        return self.x, self.y

    def contient(self, x: float, y: float) -> bool:
        """Indique si un point se trouve dans le terminal."""
        demi_largeur = self.largeur / 2
        demi_hauteur = self.hauteur / 2

        return (
            self.x - demi_largeur <= x <= self.x + demi_largeur
            and
            self.y - demi_hauteur <= y <= self.y + demi_hauteur
        )


# ============================================================
# ÉLÉMENTS DE CARTE
# ============================================================

@dataclass
class Route:
    """Voie de circulation ou route principale de l'aéroport."""

    nom: str

    points: list[tuple[int, int]]

    largeur: int = 8


@dataclass
class Aire:
    """
    Zone générale de l'aéroport.

    Exemple :
    - parking
    - fret
    - maintenance
    - aérogare
    - zone technique
    """

    nom: str

    x: int
    y: int

    largeur: int
    hauteur: int

    type_zone: str


# ============================================================
# AÉROPORT
# ============================================================

@dataclass
class Aeroport:
    """Décrit l'ensemble d'un aéroport."""

    code_icao: str
    code_iata: str
    nom: str

    centre: tuple[int, int] = (600, 600)

    pistes: list[Piste] = field(default_factory=list)

    terminaux: list[Terminal] = field(default_factory=list)

    routes: list[Route] = field(default_factory=list)

    zones: list[Aire] = field(default_factory=list)


# ============================================================
# PARIS - CHARLES DE GAULLE
# ============================================================

CDG = Aeroport(
    code_icao="LFPG",
    code_iata="CDG",
    nom="Paris - Charles de Gaulle",

    centre=(600, 600),

    pistes=[
        Piste(
            nom="08L/26R",
            cap=85,
            longueur=m_vers_radar(4215),
            decalage_y=-150,
        ),

        Piste(
            nom="09L/27R",
            cap=86,
            longueur=m_vers_radar(2700),
            decalage_y=-50,
        ),

        Piste(
            nom="09R/27L",
            cap=86,
            longueur=m_vers_radar(4200),
            decalage_y=50,
        ),

        Piste(
            nom="08R/26L",
            cap=85,
            longueur=m_vers_radar(2700),
            decalage_y=150,
        ),
    ],

    # --------------------------------------------------------
    # TERMINAUX
    # --------------------------------------------------------
    #
    # Les positions sont volontairement adaptées à l'échelle
    # de la carte du jeu.
    #
    # Elles suivent l'organisation générale réelle de CDG :
    # T1 à l'ouest, T2 au centre/sud et T3 entre les zones.
    # --------------------------------------------------------

    terminaux=[
        Terminal(
            nom="T1",
            x=330,
            y=450,
            largeur=90,
            hauteur=90,
        ),

        Terminal(
            nom="T3",
            x=430,
            y=510,
            largeur=100,
            hauteur=55,
        ),

        Terminal(
            nom="T2A",
            x=590,
            y=500,
            largeur=85,
            hauteur=45,
        ),

        Terminal(
            nom="T2B",
            x=680,
            y=500,
            largeur=75,
            hauteur=45,
        ),

        Terminal(
            nom="T2C",
            x=770,
            y=500,
            largeur=75,
            hauteur=45,
        ),

        Terminal(
            nom="T2D",
            x=860,
            y=500,
            largeur=75,
            hauteur=45,
        ),

        Terminal(
            nom="T2E",
            x=680,
            y=610,
            largeur=150,
            hauteur=55,
        ),

        Terminal(
            nom="T2F",
            x=850,
            y=610,
            largeur=120,
            hauteur=55,
        ),

        Terminal(
            nom="T2G",
            x=950,
            y=540,
            largeur=70,
            hauteur=45,
        ),
    ],

    # --------------------------------------------------------
    # ROUTES PRINCIPALES
    # --------------------------------------------------------

    routes=[
        Route(
            nom="Axe_T1_T2",
            points=[
                (330, 570),
                (450, 570),
                (600, 570),
                (800, 570),
                (950, 570),
            ],
            largeur=10,
        ),

        Route(
            nom="Acces_T2",
            points=[
                (500, 700),
                (600, 650),
                (700, 650),
                (850, 650),
                (1000, 600),
            ],
            largeur=8,
        ),
    ],

    # --------------------------------------------------------
    # ZONES
    # --------------------------------------------------------

    zones=[
        Aire(
            nom="Zone cargo",
            x=980,
            y=420,
            largeur=130,
            hauteur=100,
            type_zone="cargo",
        ),

        Aire(
            nom="Maintenance",
            x=350,
            y=700,
            largeur=130,
            hauteur=90,
            type_zone="maintenance",
        ),
    ],
)


# ============================================================
# FRANCFORT
# ============================================================

FRANCFORT = Aeroport(
    code_icao="EDDF",
    code_iata="FRA",
    nom="Frankfurt am Main",

    centre=(600, 600),

    pistes=[
        Piste(
            nom="07L/25R",
            cap=70,
            longueur=m_vers_radar(2800),
            decalage_x=-130,
        ),

        Piste(
            nom="07C/25C",
            cap=70,
            longueur=m_vers_radar(4000),
            decalage_x=0,
        ),

        Piste(
            nom="07R/25L",
            cap=70,
            longueur=m_vers_radar(4000),
            decalage_x=130,
        ),

        Piste(
            nom="18",
            cap=180,
            longueur=m_vers_radar(4000),
            decalage_x=230,
        ),
    ],

    # --------------------------------------------------------
    # TERMINAUX
    # --------------------------------------------------------

    terminaux=[
        Terminal(
            nom="T1",
            x=520,
            y=500,
            largeur=170,
            hauteur=80,
        ),

        Terminal(
            nom="T3",
            x=850,
            y=560,
            largeur=190,
            hauteur=90,
        ),
    ],

    routes=[
        Route(
            nom="Axe_T1_T3",
            points=[
                (450, 620),
                (550, 620),
                (700, 620),
                (850, 620),
            ],
            largeur=10,
        ),
    ],

    zones=[
        Aire(
            nom="Zone cargo",
            x=950,
            y=400,
            largeur=150,
            hauteur=100,
            type_zone="cargo",
        ),

        Aire(
            nom="Maintenance",
            x=350,
            y=700,
            largeur=140,
            hauteur=100,
            type_zone="maintenance",
        ),
    ],
)


# ============================================================
# AÉROPORTS DISPONIBLES
# ============================================================

AEROPORTS_DISPONIBLES = [
    CDG,
    FRANCFORT,
]