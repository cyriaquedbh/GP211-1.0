"""Conventions d'unités de la simulation (système métrique, un seul partout).

- distances radar : 1 unité = 20 m réels
- altitudes : mètres (m)
- vitesses (avions ET vent) : kilomètres/heure (km/h)
- durées : secondes (s) — la simulation tourne en temps réel
- caps / directions : degrés (°), 0 = nord, sens horaire
"""

ECHELLE_METRES_PAR_UNITE = 20

# Pente d'approche « jeu » : mètres d'altitude par unité radar de distance au point
# de toucher. Une vraie pente de 3° (~1 m/unité) imposerait de démarrer la descente
# à 50 km de la piste, bien au-delà de la zone radar : on utilise donc une pente
# adaptée à l'échelle d'affichage.
PENTE_APPROCHE = 8.0


def m_vers_radar(longueur_m: float) -> int:
    """Convertit une distance en mètres vers l'échelle d'affichage radar."""
    return round(longueur_m / ECHELLE_METRES_PAR_UNITE)


def kmh_vers_unites_par_seconde(vitesse_kmh: float) -> float:
    """Convertit une vitesse en km/h en unités radar par seconde."""
    return vitesse_kmh / 3.6 / ECHELLE_METRES_PAR_UNITE
