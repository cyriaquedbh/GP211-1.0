from dataclasses import dataclass, field


@dataclass
class Piste:
    nom: str
    cap: int
    longueur: int = 300   # "longueur jouable" sur le radar (abstraction du monde réel)
    largeur: int = 40     # "largeur jouable"

    def cap_oppose(self):
        return (self.cap + 180) % 360


@dataclass
class Aeroport:
    code_icao: str
    code_iata: str
    nom: str
    pistes: list = field(default_factory=list)

    def piste_principale(self) -> Piste:
        return self.pistes[0]


CDG = Aeroport(
    code_icao="LFPG", code_iata="CDG", nom="Paris - Charles de Gaulle",
    pistes=[
        Piste("08L/26R", 85),
        Piste("08R/26L", 85),
        Piste("09L/27R", 86),
        Piste("09R/27L", 86),
    ],
)

FRANCFORT = Aeroport(
    code_icao="EDDF", code_iata="FRA", nom="Frankfurt am Main",
    pistes=[
        Piste("07L/25R", 70),
        Piste("07C/25C", 70),
        Piste("07R/25L", 70),
        Piste("18", 180),
    ],
)

AEROPORTS_DISPONIBLES = [CDG, FRANCFORT]