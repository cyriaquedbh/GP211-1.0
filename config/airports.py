from dataclasses import dataclass, field

# 1 unité radar = 20 mètres réels (pour que les pistes tiennent dans la zone de jeu)
ECHELLE_METRES_PAR_UNITE = 20


def m_vers_radar(longueur_m: int) -> int:
    return round(longueur_m / ECHELLE_METRES_PAR_UNITE)


@dataclass
class Piste:
    nom: str
    cap: int
    longueur: int              # en unités radar, dérivée de la longueur réelle
    largeur: int = 34          # largeur "jouable", volontairement exagérée
    decalage_x: int = 0        # position de l'axe de piste par rapport au centre de l'aéroport
    decalage_y: int = 0

    def cap_oppose(self) -> int:
        return (self.cap + 180) % 360

    def centre(self, centre_aeroport):
        return (centre_aeroport[0] + self.decalage_x, centre_aeroport[1] + self.decalage_y)


@dataclass
class Aeroport:
    code_icao: str
    code_iata: str
    nom: str
    pistes: list = field(default_factory=list)


CDG = Aeroport(
    code_icao="LFPG", code_iata="CDG", nom="Paris - Charles de Gaulle",
    pistes=[
        Piste("08L/26R", 85, m_vers_radar(4215), decalage_y=-135),
        Piste("09L/27R", 86, m_vers_radar(2700), decalage_y=-45),
        Piste("09R/27L", 86, m_vers_radar(4200), decalage_y=45),
        Piste("08R/26L", 85, m_vers_radar(2700), decalage_y=135),
    ],
)

FRANCFORT = Aeroport(
    code_icao="EDDF", code_iata="FRA", nom="Frankfurt am Main",
    pistes=[
        Piste("07L/25R", 70, m_vers_radar(2800), decalage_x=-110),
        Piste("07C/25C", 70, m_vers_radar(4000), decalage_x=0),
        Piste("07R/25L", 70, m_vers_radar(4000), decalage_x=110),
        Piste("18", 180, m_vers_radar(4000), decalage_x=200),
    ],
)

AEROPORTS_DISPONIBLES = [CDG, FRANCFORT]