from abc import ABC, abstractmethod


class Instruction(ABC):
    """Classe abstraite de base représentant un ordre ATC envoyé à un avion."""

    def __init__(self, avion):
        self.avion = avion

    @abstractmethod
    def executer(self) -> None:
        """Exécute la commande sur l'appareil ciblé."""
        ...

    def __str__(self) -> str:
        return f"[{self.avion.name}] {self.__class__.__name__}"

    def __repr__(self) -> str:
        return self.__str__()


class ChangerCap(Instruction):
    """Ordre de modification de cap magnétique (0° à 359°)."""

    def __init__(self, avion, nouveau_cap: int):
        super().__init__(avion)
        self.nouveau_cap = int(nouveau_cap) % 360

    def executer(self) -> None:
        self.avion.changer_cap(self.nouveau_cap)

    def __str__(self) -> str:
        return f"[{self.avion.name}] CAP {self.nouveau_cap:03d}°"


class Monter(Instruction):
    """Ordre de changement d'altitude positif."""

    def __init__(self, avion, delta: int = 500):
        super().__init__(avion)
        self.delta = delta

    def executer(self) -> None:
        self.avion.monter(self.delta)

    def __str__(self) -> str:
        return f"[{self.avion.name}] MONTER +{self.delta}m"


class Descendre(Instruction):
    """Ordre de changement d'altitude négatif."""

    def __init__(self, avion, delta: int = 500):
        super().__init__(avion)
        self.delta = delta

    def executer(self) -> None:
        self.avion.descendre(self.delta)

    def __str__(self) -> str:
        return f"[{self.avion.name}] DESCENDRE -{self.delta}m"


class Atterrir(Instruction):
    """Ordre d'alignement et d'approche finale sur piste."""

    def __init__(self, avion, piste):
        super().__init__(avion)
        self.piste = piste

    def executer(self) -> None:
        if self.piste is not None:
            self.avion.demander_atterrissage(self.piste)

    def __str__(self) -> str:
        nom_piste = self.piste.nom if self.piste else "INCONNUE"
        return f"[{self.avion.name}] APPROCHE PISTE {nom_piste}"