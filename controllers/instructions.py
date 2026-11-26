from abc import ABC, abstractmethod
from dataclasses import dataclass

from models.avion import Avion
from models.vent import Vent


@dataclass(frozen=True)
class Retour:
    """Résultat d'une instruction : appliquée ou non, message lisible, manœuvres annulées."""

    ok: bool
    message: str
    annulations: tuple[str, ...] = ()


class Instruction(ABC):
    """Classe abstraite de base représentant un ordre ATC envoyé à un avion."""

    def __init__(self, avion: Avion) -> None:
        self.avion = avion

    @abstractmethod
    def executer(self) -> Retour:
        """Exécute la commande sur l'appareil ciblé et décrit le résultat."""
        ...

    def _manoeuvres_en_cours(self) -> frozenset[str]:
        manoeuvres = set()
        if self.avion.is_holding:
            manoeuvres.add("ATTENTE")
        if self.avion.is_landing:
            manoeuvres.add("APPROCHE")
        return frozenset(manoeuvres)

    def _retour_ok(self, avant: frozenset[str]) -> Retour:
        """Retour positif, qui signale les manœuvres annulées par l'ordre."""
        annulees = tuple(sorted(avant - self._manoeuvres_en_cours()))
        message = str(self)
        if annulees:
            suffixe = "ANNULÉE" if len(annulees) == 1 else "ANNULÉES"
            message += f" — {' + '.join(annulees)} {suffixe}"
        return Retour(True, message, annulees)

    def __str__(self) -> str:
        return f"[{self.avion.name}] {self.__class__.__name__}"

    def __repr__(self) -> str:
        return self.__str__()


class ChangerCap(Instruction):
    def __init__(self, avion: Avion, nouveau_cap: float) -> None:
        super().__init__(avion)
        self.nouveau_cap = int(nouveau_cap) % 360

    def executer(self) -> Retour:
        avant = self._manoeuvres_en_cours()
        self.avion.changer_cap(self.nouveau_cap)
        return self._retour_ok(avant)

    def __str__(self) -> str:
        return f"[{self.avion.name}] CAP {self.nouveau_cap:03d}°"


class Monter(Instruction):
    def __init__(self, avion: Avion, delta: int = 500) -> None:
        super().__init__(avion)
        self.delta = delta

    def executer(self) -> Retour:
        if self.delta <= 0:
            return Retour(False, f"[{self.avion.name}] ORDRE INVALIDE")
        avant = self._manoeuvres_en_cours()
        self.avion.monter(self.delta)
        return self._retour_ok(avant)

    def __str__(self) -> str:
        return f"[{self.avion.name}] MONTER +{self.delta}m"


class Descendre(Instruction):
    def __init__(self, avion: Avion, delta: int = 500) -> None:
        super().__init__(avion)
        self.delta = delta

    def executer(self) -> Retour:
        if self.delta <= 0:
            return Retour(False, f"[{self.avion.name}] ORDRE INVALIDE")
        avant = self._manoeuvres_en_cours()
        self.avion.descendre(self.delta)
        return self._retour_ok(avant)

    def __str__(self) -> str:
        return f"[{self.avion.name}] DESCENDRE -{self.delta}m"


class Atterrir(Instruction):
    SEUIL_VENT_ARRIERE = 5.0  # km/h

    def __init__(
        self,
        avion: Avion,
        piste,
        vent: Vent | None = None,
        centre: tuple[int, int] = (0, 0),
    ) -> None:
        super().__init__(avion)
        self.piste = piste
        self.vent = vent
        self.centre = centre

    def executer(self) -> Retour:
        if self.piste is None or not self.avion.demander_atterrissage(self.piste, self.centre):
            return Retour(False, f"[{self.avion.name}] AUCUNE PISTE DISPONIBLE")

        message = str(self)
        if self.vent is not None:
            cap = self.piste.cap_atterrissage(self.avion.sens_approche)
            face = self.vent.composante_face(cap)
            if face < -self.SEUIL_VENT_ARRIERE:
                message += f" — ⚠ VENT ARRIÈRE {abs(int(face))} km/h"
        return Retour(True, message)

    def __str__(self) -> str:
        nom_piste = self.piste.nom if self.piste else "INCONNUE"
        return f"[{self.avion.name}] APPROCHE PISTE {nom_piste}"


class Attendre(Instruction):
    """Ordre de mise en circuit d'attente (Holding Pattern)."""

    def executer(self) -> Retour:
        avant = self._manoeuvres_en_cours()
        self.avion.effectuer_attente()
        return self._retour_ok(avant)

    def __str__(self) -> str:
        return f"[{self.avion.name}] CIRCUIT D'ATTENTE"
