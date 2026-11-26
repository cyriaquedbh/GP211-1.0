"""Tests de la logique de simulation (sans interface graphique).

Lancer depuis la racine du projet :  python -m unittest discover -s tests -v
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.airports import CDG, Piste  # noqa: E402
from config.unites import kmh_vers_unites_par_seconde  # noqa: E402
from controllers.instructions import Attendre, Atterrir, ChangerCap, Descendre  # noqa: E402
from controllers.simulation_engine import SimulationEngine  # noqa: E402
from models.avion import Avion  # noqa: E402
from models.vent import Vent  # noqa: E402

CENTRE = (0, 0)
DT = 0.05


def creer_avion(x=0.0, y=0.0, cap=0.0, altitude=3000.0, vitesse=400.0, nom="T1") -> Avion:
    avion = Avion(nom)
    avion.x, avion.y = x, y
    avion.cap = avion.target_cap = float(cap)
    avion.altitude = avion.target_altitude = float(altitude)
    avion.vitesse = avion.vitesse_croisiere = float(vitesse)
    return avion


def avion_sur_axe(piste: Piste, distance_seuil_centre: float, altitude: float) -> Avion:
    """Avion aligné sur l'axe de la piste, en amont, cap de piste."""
    dir_x, dir_y = piste.direction()
    cx, cy = piste.centre(CENTRE)
    p = -distance_seuil_centre
    return creer_avion(cx + dir_x * p, cy + dir_y * p, piste.cap, altitude)


class TestUnites(unittest.TestCase):
    def test_conversion_vitesse(self):
        # 72 km/h = 20 m/s = 1 unité radar (20 m) par seconde
        self.assertAlmostEqual(kmh_vers_unites_par_seconde(72), 1.0)

    def test_vent_face_et_arriere(self):
        vent = Vent()
        vent.direction, vent.vitesse = 90, 20
        self.assertAlmostEqual(vent.composante_face(90), 20.0)
        self.assertAlmostEqual(vent.composante_face(270), -20.0)
        self.assertAlmostEqual(vent.composante_face(0), 0.0, places=6)


class TestPiste(unittest.TestCase):
    def test_position_relative(self):
        piste = Piste(nom="09", cap=90, longueur=100, largeur=10)
        proj, lat = piste.position_relative(-100, 0, CENTRE)
        self.assertAlmostEqual(proj, -100)
        self.assertAlmostEqual(lat, 0)
        proj, lat = piste.position_relative(0, 10, CENTRE)
        self.assertAlmostEqual(proj, 0)
        self.assertAlmostEqual(lat, 10)

    def test_sens_approche(self):
        piste = Piste(nom="09", cap=90, longueur=100)
        self.assertEqual(piste.sens_approche(-50), 1)
        self.assertEqual(piste.sens_approche(50), -1)
        self.assertEqual(piste.cap_atterrissage(1), 90)
        self.assertEqual(piste.cap_atterrissage(-1), 270)


class TestIndependanceDuPas(unittest.TestCase):
    def test_meme_trajectoire_quel_que_soit_dt(self):
        a = creer_avion(cap=45)
        b = creer_avion(cap=45)
        a.update(1.0)
        for _ in range(20):
            b.update(0.05)
        self.assertAlmostEqual(a.x, b.x, places=6)
        self.assertAlmostEqual(a.y, b.y, places=6)
        self.assertAlmostEqual(a.fuel, b.fuel, places=6)


class TestAtterrissage(unittest.TestCase):
    def setUp(self):
        self.piste = CDG.pistes[0]

    def test_atterrissage_reussi_sur_pente(self):
        avion = avion_sur_axe(self.piste, distance_seuil_centre=250, altitude=1400)
        self.assertTrue(avion.demander_atterrissage(self.piste, CENTRE))

        atterri = False
        for _ in range(int(120 / DT)):
            avion.update(DT, CENTRE)
            self.assertFalse(avion.a_crashe(CENTRE), "ne doit pas crasher en finale")
            if avion.a_atterri(CENTRE):
                atterri = True
                break
        self.assertTrue(atterri)

    def test_descente_suit_la_pente_et_pas_directement_vers_zero(self):
        avion = avion_sur_axe(self.piste, 250, 1400)
        avion.demander_atterrissage(self.piste, CENTRE)
        for _ in range(int(10 / DT)):
            avion.update(DT, CENTRE)
        # Après 10 s, encore loin du sol : l'avion suit la pente, il ne plonge pas.
        self.assertGreater(avion.altitude, 600)
        self.assertAlmostEqual(avion.altitude, avion.altitude_ideale(CENTRE), delta=60)

    def test_remise_de_gaz_si_trop_haut(self):
        avion = avion_sur_axe(self.piste, 250, 5000)
        avion.demander_atterrissage(self.piste, CENTRE)

        evenement = None
        for _ in range(int(150 / DT)):
            avion.update(DT, CENTRE)
            evenement = evenement or avion.consommer_evenement()
            self.assertFalse(avion.a_crashe(CENTRE))
            if not avion.is_landing:
                break
        self.assertFalse(avion.is_landing)
        self.assertIsNotNone(evenement)
        self.assertIn("REMISE DE GAZ", evenement)
        self.assertGreater(avion.target_altitude, avion.altitude)

    def test_sol_hors_piste_crash(self):
        avion = creer_avion(x=300, y=300, cap=0, altitude=100)
        avion.descendre(500)
        for _ in range(int(20 / DT)):
            avion.update(DT, CENTRE)
        self.assertTrue(avion.a_crashe(CENTRE))

    def test_pas_d_alerte_sol_en_finale(self):
        avion = avion_sur_axe(self.piste, 100, 300)
        avion.demander_atterrissage(self.piste, CENTRE)
        self.assertFalse(avion.en_alerte)


class TestOrdres(unittest.TestCase):
    def test_changer_cap_annule_attente_avec_retour(self):
        avion = creer_avion()
        Attendre(avion).executer()
        self.assertTrue(avion.is_holding)
        retour = ChangerCap(avion, 120).executer()
        self.assertTrue(retour.ok)
        self.assertFalse(avion.is_holding)
        self.assertIn("ATTENTE", retour.annulations)
        self.assertIn("ANNULÉE", retour.message)

    def test_monter_apres_approche_part_de_l_altitude_courante(self):
        piste = CDG.pistes[0]
        avion = avion_sur_axe(piste, 250, 1400)
        avion.demander_atterrissage(piste, CENTRE)
        for _ in range(int(5 / DT)):
            avion.update(DT, CENTRE)
        altitude = avion.altitude
        retour = Descendre(avion, 100).executer()
        self.assertIn("APPROCHE", retour.annulations)
        self.assertAlmostEqual(avion.target_altitude, altitude - 100)

    def test_atterrir_sans_piste(self):
        retour = Atterrir(creer_avion(), None).executer()
        self.assertFalse(retour.ok)

    def test_alerte_vent_arriere(self):
        piste = CDG.pistes[0]
        avion = avion_sur_axe(piste, 250, 1400)
        vent = Vent()
        vent.direction, vent.vitesse = (piste.cap + 180) % 360, 20  # vent venant de l'arrière
        retour = Atterrir(avion, piste, vent, CENTRE).executer()
        self.assertTrue(retour.ok)
        self.assertIn("VENT ARRIÈRE", retour.message)

    def test_attente_tourne_en_continu(self):
        avion = creer_avion(cap=0)
        Attendre(avion).executer()
        for _ in range(int(30 / DT)):
            avion.update(DT, CENTRE)
        self.assertAlmostEqual(avion.cap, (Avion.TAUX_VIRAGE * 30) % 360, delta=1.0)
        self.assertAlmostEqual(avion.target_cap, avion.cap)


class TestMoteur(unittest.TestCase):
    def nouveau_moteur(self, avions):
        moteur = SimulationEngine(CDG)
        moteur.prochain_spawn = 1e9
        moteur.avions = avions
        return moteur

    def test_collision_termine_la_partie(self):
        moteur = self.nouveau_moteur([creer_avion(nom="A"), creer_avion(nom="B")])
        self.assertTrue(moteur.maj(DT))
        self.assertTrue(moteur.partie_terminee)
        self.assertEqual(moteur.raison_fin, "COLLISION EN VOL")
        self.assertTrue(moteur.maj(DT))  # figé après la fin

    def test_panne_seche(self):
        avion = creer_avion(x=10, y=10)
        avion.fuel = 0.0
        moteur = self.nouveau_moteur([avion])
        moteur.maj(DT)
        self.assertEqual(moteur.crashes, 1)
        self.assertEqual(moteur.avions, [])

    def test_sortie_de_secteur(self):
        avion = creer_avion(x=SimulationEngine.RAYON_SECTEUR + 10, y=0, cap=90)
        moteur = self.nouveau_moteur([avion])
        moteur.score = 300
        moteur.maj(DT)
        self.assertEqual(moteur.sorties_secteur, 1)
        self.assertEqual(moteur.score, 300 - SimulationEngine.PENALITE_SORTIE)
        self.assertEqual(moteur.avions, [])

    def test_evenement_expire(self):
        moteur = self.nouveau_moteur([creer_avion()])
        moteur._signaler("TEST")
        self.assertEqual(moteur.evenement_recent, "TEST")
        moteur.temps_ecoule += SimulationEngine.DUREE_EVENEMENT + 1
        self.assertEqual(moteur.evenement_recent, "")

    def test_apparition_sur_le_cercle_vers_le_centre(self):
        moteur = SimulationEngine(CDG)
        for avion in moteur.avions:
            rayon = math.hypot(avion.x, avion.y)
            self.assertAlmostEqual(rayon, moteur.zone_taille / 2 + Avion.MARGE_SPAWN, places=6)
            cap_vers_centre = math.degrees(math.atan2(-avion.x, avion.y)) % 360
            ecart = abs((avion.cap - cap_vers_centre + 540) % 360 - 180)
            self.assertLessEqual(ecart, Avion.ECART_CAP_SPAWN + 1e-6)

    def test_atterrissage_compte_les_points(self):
        piste = CDG.pistes[0]
        avion = avion_sur_axe(piste, 250, 1400)
        avion.demander_atterrissage(piste, CENTRE)
        moteur = self.nouveau_moteur([avion])
        for _ in range(int(120 / DT)):
            moteur.maj(DT)
            if not moteur.avions:
                break
        self.assertEqual(moteur.atterrissages_reussis, 1)
        self.assertEqual(moteur.score, SimulationEngine.POINTS_ATTERRISSAGE)

    def test_choix_piste_prefere_face_au_vent(self):
        # Deux pistes de même centre, caps opposés : on choisit celle dont on atterrit face au vent.
        pistes = [Piste("A", 90, 100), Piste("B", 0, 100)]
        moteur = SimulationEngine(CDG)
        moteur.aeroport = type(CDG)("TEST", "TST", "Test", pistes)
        moteur.vent.direction, moteur.vent.vitesse = 0, 40  # vent du nord
        avion = creer_avion(x=0, y=300)  # au sud : approche piste B au cap 0 = face au vent
        self.assertEqual(moteur.piste_pour_atterrissage(avion).nom, "B")


if __name__ == "__main__":
    unittest.main()
