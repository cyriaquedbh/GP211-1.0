import math
import random


class Avion:
    def __init__(self, name: str, zone_taille: int = 600):
        self.name = name
        self.x = random.uniform(50, zone_taille - 50)
        self.y = random.uniform(50, zone_taille - 50)
        self.altitude = random.randint(2000, 5000)
        self.target_altitude = self.altitude
        self.vitesse = random.randint(300, 500)
        self.cap = random.randint(0, 359)
        self.fuel = 100.0
        self.selected = False
        self.is_landing = False

    def changer_cap(self, nouveau_cap: int):
        self.cap = nouveau_cap % 360
        self.is_landing = False

    def monter(self, delta: int = 500):
        self.target_altitude += delta
        self.is_landing = False

    def descendre(self, delta: int = 500):
        self.target_altitude = max(0, self.target_altitude - delta)
        self.is_landing = False

    def demander_atterrissage(self):
        self.is_landing = True
        self.target_altitude = 0

    def update(self, dt: float, centre=(300, 300)):
        if self.altitude < self.target_altitude:
            self.altitude += min(20, self.target_altitude - self.altitude)
        elif self.altitude > self.target_altitude:
            self.altitude -= min(20, self.altitude - self.target_altitude)

        if self.is_landing:
            cx, cy = centre
            dx, dy = cx - self.x, cy - self.y
            angle_cible = math.degrees(math.atan2(dx, -dy)) % 360
            diff = (angle_cible - self.cap + 180) % 360 - 180
            if abs(diff) > 2:
                self.cap += 2 if diff > 0 else -2
            self.cap %= 360

        rad = math.radians(self.cap)
        self.x += math.sin(rad) * (self.vitesse / 100) * dt
        self.y -= math.cos(rad) * (self.vitesse / 100) * dt
        self.fuel = max(0.0, self.fuel - 0.1 * dt)

    def a_atterri(self, centre=(300, 300), rayon=50) -> bool:
        cx, cy = centre
        distance = math.hypot(self.x - cx, self.y - cy)
        return self.is_landing and self.altitude <= 0 and distance < rayon