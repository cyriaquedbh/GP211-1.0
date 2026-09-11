from abc import ABC, abstractmethod


class Instruction(ABC):
    def __init__(self, avion):
        self.avion = avion

    @abstractmethod
    def executer(self):
        ...

    def __str__(self):
        return f"{self.__class__.__name__} -> {self.avion.name}"


class ChangerCap(Instruction):
    def __init__(self, avion, nouveau_cap: int):
        super().__init__(avion)
        self.nouveau_cap = nouveau_cap

    def executer(self):
        self.avion.changer_cap(self.nouveau_cap)


class Monter(Instruction):
    def __init__(self, avion, delta: int = 500):
        super().__init__(avion)
        self.delta = delta

    def executer(self):
        self.avion.monter(self.delta)


class Descendre(Instruction):
    def __init__(self, avion, delta: int = 500):
        super().__init__(avion)
        self.delta = delta

    def executer(self):
        self.avion.descendre(self.delta)


class Atterrir(Instruction):
    def __init__(self, avion, piste):
        super().__init__(avion)
        self.piste = piste

    def executer(self):
        self.avion.demander_atterrissage(self.piste)