from dataclasses import dataclass, field

# 1 unité radar = 20 mètres réels
ECHELLE_METRES_PAR_UNITE = 20


def m_vers_radar(longueur_m: int) -> int:
    """Convertit une distance en mètres vers l'échelle d'affichage radar."""
    return round(longueur_m / ECHELLE_METRES_PAR_UNITE)


@dataclass
class Piste:
    nom: str
    cap: int
    longueur: int
    largeur: int = 34
    decalage_x: int = 0
    decalage_y: int = 0

    def cap_oppose(self) -> int:
        return (self.cap + 180) % 360

    def centre(self, centre_aeroport: tuple[int, int]) -> tuple[int, int]:
        return (
            centre_aeroport[0] + self.decalage_x,
            centre_aeroport[1] + self.decalage_y,
        )


@dataclass
class Aeroport:
    code_icao: str
    code_iata: str
    nom: str
    pistes: list[Piste] = field(default_factory=list)


# ============================================================
# PARIS - CHARLES DE GAULLE (LFPG)
# ============================================================

CDG = Aeroport(
    code_icao="LFPG",
    code_iata="CDG",
    nom="Paris - Charles de Gaulle",
    pistes=[
        Piste(
            nom="08L/26R",
            cap=85,
            longueur=m_vers_radar(4215),
            largeur=34,
            decalage_y=-135,
        ),
        Piste(
            nom="09L/27R",
            cap=86,
            longueur=m_vers_radar(2700),
            largeur=34,
            decalage_y=-45,
        ),
        Piste(
            nom="09R/27L",
            cap=86,
            longueur=m_vers_radar(4200),
            largeur=34,
            decalage_y=45,
        ),
        Piste(
            nom="08R/26L",
            cap=85,
            longueur=m_vers_radar(2700),
            largeur=34,
            decalage_y=135,
        ),
    ],
)


# ============================================================
# FRANCFORT - FRANKFURT AM MAIN (EDDF)
# ============================================================

FRANCFORT = Aeroport(
    code_icao="EDDF",
    code_iata="FRA",
    nom="Frankfurt am Main",
    pistes=[
        Piste(
            nom="07L/25R",
            cap=70,
            longueur=m_vers_radar(2800),
            largeur=34,
            decalage_x=-110,
        ),
        Piste(
            nom="07C/25C",
            cap=70,
            longueur=m_vers_radar(4000),
            largeur=34,
            decalage_x=0,
        ),
        Piste(
            nom="07R/25L",
            cap=70,
            longueur=m_vers_radar(4000),
            largeur=34,
            decalage_x=110,
        ),
        Piste(
            nom="18",
            cap=180,
            longueur=m_vers_radar(4000),
            largeur=34,
            decalage_x=200,
        ),
    ],
)


# Liste des aéroports disponibles
AEROPORTS_DISPONIBLES = [
    CDG,
    FRANCFORT,
]