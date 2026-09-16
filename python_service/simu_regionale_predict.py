from pathlib import Path
import csv
import re
import unicodedata
import duckdb

from datetime import datetime
from extraction_json import charger_donnees
from simu_nationale import EPSILON, enregistrer_productions, verifier_rampes
from metrique_centrale import router_deficit


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path("/app/base_analytique.duckdb")
CSV_PATH_DOCKER = Path("/app/predictions/previsions_1an.csv")
CSV_PATH_LOCAL = BASE_DIR / "predictions" / "previsions_1an.csv"
CSV_PATH_OLD = BASE_DIR.parent / "predict_service" / "predictions" / "previsions_1an.csv"
if CSV_PATH_DOCKER.exists():
    CSV_PATH = CSV_PATH_DOCKER
elif CSV_PATH_LOCAL.exists():
    CSV_PATH = CSV_PATH_LOCAL
else:
    CSV_PATH = CSV_PATH_OLD
data = charger_donnees()

# ============================================================
# GESTION DES PERTURBATIONS DE CONSOMMATION
# ============================================================

_scenarios_actifs = []

def indexer_points_par_date_heure(points):
    return {(point["date"], point["heure"]): point for point in points}

def _appliquer_une_perturbation_prevision(previsions_par_region, id_region, date_debut, heure_debut, date_fin, heure_fin, deltaMw ):
    id_region = normaliser_region(id_region)

    if id_region not in previsions_par_region:
        raise ValueError(
            f"Région inconnue dans les prévisions : {id_region}"
        )

    previsions_region = previsions_par_region[id_region]

    debut = (date_debut, heure_debut)
    fin = (date_fin, heure_fin)

    if debut > fin:
        raise ValueError(
            "La date/heure de début doit être antérieure "
            "ou égale à la date/heure de fin."
        )

    points_modifies = []

    for point in previsions_region:

        point_date_heure = (
            point["date"],
            point["heure"]
        )

        if debut <= point_date_heure <= fin:

            ancienne_valeur = point["consommation_mw"]

            point["consommation_mw"] += deltaMw

            points_modifies.append({
                "date": point["date"],
                "heure": point["heure"],
                "ancienne_consommation_mw": ancienne_valeur,
                "nouvelle_consommation_mw": point["consommation_mw"],
                "deltaMw": deltaMw
            })

    if not points_modifies:
        raise ValueError(
            f"Aucun point de prévision trouvé entre "
            f"{date_debut} {heure_debut} et "
            f"{date_fin} {heure_fin} "
            f"pour la région {id_region}."
        )

    return {
        "region": id_region,
        "date_debut": date_debut,
        "heure_debut": heure_debut,
        "date_fin": date_fin,
        "heure_fin": heure_fin,
        "deltaMw": deltaMw,
        "nombre_points_modifies": len(points_modifies),
        "points_modifies": points_modifies
    }


def perturber_consommation_predict(id_region, date_debut, heure_debut, date_fin, heure_fin, deltaMw):

    deltaMw = float(deltaMw)

    scenario = {
        "id_region": normaliser_region(id_region),
        "date_debut": date_debut,
        "heure_debut": heure_debut,
        "date_fin": date_fin,
        "heure_fin": heure_fin,
        "deltaMw": deltaMw
    }

    _scenarios_actifs.append(scenario)

    return {
        "scenarios_actifs": list(_scenarios_actifs)
    }


def previsions_avec_perturbations():
    # Recharge les prévisions originales puis applique tous les scénarios actifs.

    previsions = charger_previsions_consommation()

    for scenario in _scenarios_actifs:

        _appliquer_une_perturbation_prevision(
            previsions,
            scenario["id_region"],
            scenario["date_debut"],
            scenario["heure_debut"],
            scenario["date_fin"],
            scenario["heure_fin"],
            scenario["deltaMw"]
        )

    return previsions


def reinitialiser_scenario():
    # Supprime toutes les perturbations actives.

    global _scenarios_actifs

    _scenarios_actifs = []

    return {
        "status": "reinitialise"
    }


def normaliser_region(nom):
    nom = nom.strip().lower()
    nom = unicodedata.normalize("NFKD", nom)
    nom = "".join(c for c in nom if not unicodedata.combining(c))
    nom = re.sub(r"[^a-z0-9]+", "_", nom)
    return nom.strip("_")



def donnees_centrales_30_min():
    centrales_ajustees = []
    for centrale in data["params_temporels"]["plants"]:
        centrales_ajustees.append({
            "plant_id": centrale["plant_id"],
            "plant_name": centrale.get("plant_name", centrale["plant_id"]),
            "rampe_up_ajustee_30_min": centrale["max_ramp_up_mw_per_15_min"] * 2,
            "rampe_down_ajustee_30_min": centrale["max_ramp_down_mw_per_15_min"] * 2,
            "initial_output_mw_at_23_45_previous_day": centrale["initial_output_mw_at_23_45_previous_day"],
            "minimum_operating_power_mw": centrale["minimum_operating_power_mw"],
            "maximum_power_mw": centrale["maximum_power_mw"],
        })
    return centrales_ajustees


def trouver_centrale(plant_id, centrales):
    for centrale in centrales:
        if centrale["plant_id"] == plant_id:
            return centrale
    raise ValueError(f"Centrale {plant_id} introuvable")


def regions_avec_centrales():
    centrales = donnees_centrales_30_min()
    regions = []
    for region in data["parc_nucleaire"]["regions"]:
        centrales_region = [trouver_centrale(plant_id, centrales) for plant_id in region["local_plant_ids"] if not plant_id.startswith("PDL_")]
        regions.append({
            "region_id": normaliser_region(region["id"]),
            "plants": centrales_region
        })
    return regions


def initialiser_etat():
    return {
        centrale["plant_id"]: centrale["initial_output_mw_at_23_45_previous_day"]
        for centrale in donnees_centrales_30_min()
    }


def production_non_pilotables_regional_duckdb():
    con = duckdb.connect(str(DB_PATH), read_only=True)

    result = con.execute("""
        SELECT dr.region,
               strftime(dt.date, '%m-%d') AS mois_jour,
               CAST(dt.heure AS VARCHAR) AS heure,
               fe.production_eolienne_mw, fe.production_solaire_mw
        FROM dim_region AS dr
        JOIN fait_energie AS fe ON dr.id_region = fe.id_region
        JOIN dim_temps AS dt ON dt.id_temps = fe.id_temps
        WHERE dt.date >= '2025-07-01' AND dt.date < '2026-07-01'
        ORDER BY dr.region, dt.date, dt.heure
    """)

    colonnes = [desc[0] for desc in result.description]
    lignes = [dict(zip(colonnes, ligne)) for ligne in result.fetchall()]

    production_par_region = {}
    for ligne in lignes:
        region_id = normaliser_region(ligne["region"])
        if region_id not in production_par_region:
            production_par_region[region_id] = []
        ligne["heure"] = ligne["heure"][:5]
        production_par_region[region_id].append(ligne)

    con.close()
    return production_par_region


def charger_previsions_consommation():
    previsions_par_region = {}

    with open(CSV_PATH, encoding="utf-8-sig") as f:
        lecteur = csv.DictReader(f)
        for ligne in lecteur:
            region_id = normaliser_region(ligne["region"])
            heure = ligne["heure"][:5]
            mois_jour = ligne["date"][5:]

            if region_id not in previsions_par_region:
                previsions_par_region[region_id] = []

            previsions_par_region[region_id].append({
                "date": ligne["date"],
                "heure": heure,
                "mois_jour": mois_jour,
                "consommation_mw": float(ligne["consommation_predite"])
            })

    return previsions_par_region

def obtenir_prediction_consommation(id_region, date, heure):
    id_region = normaliser_region(id_region)
    heure = heure[:5]

    previsions = charger_previsions_consommation()

    if id_region not in previsions:
        raise ValueError(f"Région inconnue dans les prévisions : {id_region}")

    for point in previsions[id_region]:
        if point["date"] == date and point["heure"] == heure:
            return {
                "id_region": id_region,
                "date": point["date"],
                "heure": point["heure"],
                "consommation_predite": point["consommation_mw"]
            }

    raise ValueError(
        f"Aucune prévision trouvée pour {id_region} le {date} à {heure}."
    )

def demande_moins_non_pilotable_previsions(consommation=None):
    if consommation is None:
        consommation = previsions_avec_perturbations()

    production_np = production_non_pilotables_regional_duckdb()

    demande_residuelle = {}

    for region in consommation:
        prod_par_cle = {(p["mois_jour"], p["heure"]): p["production_eolienne_mw"] + p["production_solaire_mw"] for p in production_np.get(region, [])}

        demande_residuelle[region] = []
        manquants = 0

        for point_conso in consommation[region]:
            cle = (point_conso["mois_jour"], point_conso["heure"])
            production_totale = prod_par_cle.get(cle)

            if production_totale is None:
                manquants += 1
                continue

            demande_residuelle[region].append({
                "date": point_conso["date"],
                "heure": point_conso["heure"],
                "demande_residuelle_mw": point_conso["consommation_mw"] - production_totale
            })

        if manquants > 0:
            print(f"{region} : {manquants} points sans correspondance de production")

    return demande_residuelle


def production_non_pilotable_detail_regional():
    production_np = production_non_pilotables_regional_duckdb()

    detail = {}
    for region, points in production_np.items():
        detail[region] = {(p["mois_jour"], p["heure"]): {"solar_mw": p["production_solaire_mw"], "wind_mw": p["production_eolienne_mw"]}for p in points}
    return detail



def pourcentage_repartition_regionale(
    consommation=None,
    demande_residuelle=None
):
    regions = regions_avec_centrales()

    if consommation is None:
        consommation = previsions_avec_perturbations()

    if demande_residuelle is None:
        demande_residuelle = demande_moins_non_pilotable_previsions(
            consommation
        )

    minimum_reserve_percent = 8.0
    facteur_reserve = 1 - (minimum_reserve_percent / 100)

    pourcentage_regional = {}

    # Transformation des demandes en dictionnaires
    demande_residuelle_indexee = {
        region_id: indexer_points_par_date_heure(points)
        for region_id, points in demande_residuelle.items()
    }

    for region in regions:

        region_id = region["region_id"]

        if not region["plants"]:
            continue

        capacite_max_region = sum(
            c["maximum_power_mw"]
            for c in region["plants"]
        )

        if capacite_max_region == 0:
            continue

        capacite_dispo_region = (capacite_max_region * facteur_reserve)

        points_region = demande_residuelle_indexee.get(
            region_id,
            {}
        )

        pourcentage_regional[region_id] = {}

        for cle, point in points_region.items():

            demande = point["demande_residuelle_mw"]

            pourcentage_regional[region_id][cle] = (
                demande / capacite_dispo_region
            )

    return pourcentage_regional, facteur_reserve


def calculer_centrale_heure(centrale, pourcentage, etat_precedent):
    plant_id = centrale["plant_id"]
    production_demandee = centrale["maximum_power_mw"] * pourcentage
    production_precedente = etat_precedent[plant_id]

    minimum_technique = centrale["minimum_operating_power_mw"]
    maximum_technique = centrale["maximum_power_mw"]

    minimum_temporel = production_precedente - centrale["rampe_down_ajustee_30_min"]
    maximum_temporel = production_precedente + centrale["rampe_up_ajustee_30_min"]

    minimum_autorise = max(minimum_technique, minimum_temporel)
    maximum_autorise = min(maximum_technique, maximum_temporel)

    return {
        "plant_id": plant_id,
        "production": production_demandee,
        "production_demandee": production_demandee,
        "production_precedente": production_precedente,
        "minimum": minimum_autorise,
        "maximum": maximum_autorise,
        "minimum_technique": minimum_technique,
        "maximum_technique": maximum_technique,
        "rampe_montee": centrale["rampe_up_ajustee_30_min"],
        "rampe_descente": centrale["rampe_down_ajustee_30_min"],
    }


def construire_centrales_heure(centrales, pourcentage, etat_precedent):
    return [calculer_centrale_heure(c, pourcentage, etat_precedent) for c in centrales]


def limites_globales(centrales_heure):
    production_minimal = sum(c["minimum"] for c in centrales_heure)
    production_maximal = sum(c["maximum"] for c in centrales_heure)
    return production_minimal, production_maximal


def calculer_demande_heure(centrales_heure):
    return sum(c["production_demandee"] for c in centrales_heure)


def sous_minimum(centrales_heure, heure, productions_sous_minimum):
    surplus_a_retirer = 0
    for centrale in centrales_heure:
        if centrale["production"] < centrale["minimum"]:
            surplus = centrale["minimum"] - centrale["production"]
            surplus_a_retirer += surplus
            productions_sous_minimum.append({
                "plant_id": centrale["plant_id"],
                "heure": heure,
                "production_demandee": centrale["production_demandee"],
                "production_minimum": centrale["minimum"],
                "surplus": surplus
            })
            centrale["production"] = centrale["minimum"]
    return surplus_a_retirer


def sur_maximum(centrales_heure, heure, productions_sur_maximum):
    deficit_a_repartir = 0
    for centrale in centrales_heure:
        if centrale["production"] > centrale["maximum"]:
            deficit = centrale["production"] - centrale["maximum"]
            deficit_a_repartir += deficit
            productions_sur_maximum.append({
                "plant_id": centrale["plant_id"],
                "heure": heure,
                "production_demandee": centrale["production_demandee"],
                "production_minimum": centrale["minimum"],
                "deficit": deficit
            })
            centrale["production"] = centrale["maximum"]
    return deficit_a_repartir


def redistribuer(centrales_heure, quantite, borne, operation):
    while quantite > EPSILON:
        centrales_disponibles = [c for c in centrales_heure if borne(c)]
        if not centrales_disponibles:
            break

        variation_par_centrale = quantite / len(centrales_disponibles)
        quantite_restante = 0

        for centrale in centrales_disponibles:
            variation, reste = operation(centrale, variation_par_centrale)
            centrale["production"] += variation
            quantite_restante += reste

        quantite = quantite_restante
    return quantite


def redistribuer_surplus(centrales_heure, surplus_a_retirer):
    return redistribuer(
        centrales_heure, surplus_a_retirer,
        lambda c: c["production"] > c["minimum"] + EPSILON,
        lambda c, reduction: (
            -min(reduction, c["production"] - c["minimum"]),
            reduction - min(reduction, c["production"] - c["minimum"])
        )
    )


def redistribuer_deficit(centrales_heure, deficit_a_repartir):
    return redistribuer(
        centrales_heure, deficit_a_repartir,
        lambda c: c["production"] < c["maximum"] - EPSILON,
        lambda c, augmentation: (
            min(augmentation, c["maximum"] - c["production"]),
            augmentation - min(augmentation, c["maximum"] - c["production"])
        )
    )


def plant_id_vers_region(regions_avec_nucleaire):
    mapping = {}
    for region in regions_avec_nucleaire:
        for centrale in region["plants"]:
            mapping[centrale["plant_id"]] = region["region_id"]
    return mapping


def repartir_surplus_vers_deficits(resultats_heure):
    surplus_regions = [r for r in resultats_heure if r["surplus_residuel"] > EPSILON]
    deficit_regions = [r for r in resultats_heure if r["deficit_residuel"] > EPSILON]

    echanges = []
    index_surplus = 0

    for deficit_region in deficit_regions:
        while deficit_region["deficit_residuel"] > EPSILON and index_surplus < len(surplus_regions):
            surplus_region = surplus_regions[index_surplus]

            if surplus_region["surplus_residuel"] <= EPSILON:
                index_surplus += 1
                continue

            transfert = min(deficit_region["deficit_residuel"], surplus_region["surplus_residuel"])
            echanges.append({
                "region_source": surplus_region["region_id"],
                "region_destination": deficit_region["region_id"],
                "quantite_mw": transfert
            })
            deficit_region["deficit_residuel"] -= transfert
            surplus_region["surplus_residuel"] -= transfert

    return echanges


def resultats_regions_sans_nucleaire(regions_sans_nucleaire, demande_residuelle_indexee, date, heure, ids_deconnectees):
    resultats = []
    cle = (date, heure)

    for region in regions_sans_nucleaire:
        region_id = region["region_id"]

        if region_id in ids_deconnectees:
            continue

        points = demande_residuelle_indexee.get(region_id, {})

        point = points.get(cle)

        if point is None:
            continue

        valeur_demande = point["demande_residuelle_mw"]

        deficit = max(valeur_demande, 0)

        resultats.append({
            "region_id": region_id,
            "demande_mw": valeur_demande,
            "production_mw": 0,
            "maximum_regional_mw": 0,
            "surplus_residuel": 0,
            "deficit_residuel": deficit
        })

    return resultats


def capacite_max_par_region(regions_avec_nucleaire):
    return {
        region["region_id"]: sum(c["maximum_power_mw"] for c in region["plants"])
        for region in regions_avec_nucleaire
    }


def detecter_situation_degradee(region_id, heure, production_mw, maximum_regional_mw, capacite_max_region, minimum_reserve_percent):
    reserve_disponible_mw = maximum_regional_mw - production_mw
    reserve_disponible_percent = (reserve_disponible_mw / capacite_max_region * 100) if capacite_max_region > 0 else 0
    situation_degradee = reserve_disponible_percent < minimum_reserve_percent

    return {
        "region_id": region_id,
        "heure": heure,
        "production_mw": production_mw,
        "maximum_technique_mw": maximum_regional_mw,
        "capacite_max_region_mw": capacite_max_region,
        "reserve_disponible_mw": reserve_disponible_mw,
        "reserve_disponible_percent": reserve_disponible_percent,
        "seuil_minimum_percent": minimum_reserve_percent,
        "situation_degradee": situation_degradee,
    }


def construire_detail_regional(region_id, date, heure, production_mw, production_precedente_mw, consommation_indexee, non_pilotable_detail, demande_residuelle_indexee):
    variation_mw = production_mw - production_precedente_mw

    if variation_mw > EPSILON:
        sens_variation = "hausse"
    elif variation_mw < -EPSILON:
        sens_variation = "baisse"
    else:
        sens_variation = "stable"

    cle = (date, heure)

    # Consommation
    point_consommation = consommation_indexee.get(
        region_id, {}
    ).get(cle)

    if point_consommation is None:
        raise ValueError(
            f"Aucune consommation trouvée pour "
            f"{region_id} à {date} {heure}"
        )


    # Production non pilotable
    detail_np = non_pilotable_detail.get(
        region_id, {}
    ).get(
        cle,
        {
            "solar_mw": 0,
            "wind_mw": 0
        }
    )

    # Demande résiduelle
    point_demande = demande_residuelle_indexee.get(
        region_id, {}
    ).get(cle)

    if point_demande is None:
        raise ValueError(
            f"Aucune demande résiduelle trouvée pour "
            f"{region_id} à {date} {heure}"
        )

    return {
        "region_id": region_id,
        "date": date,
        "heure": heure,

        "consommation_mw": point_consommation["consommation_mw"],

        "solar_mw": detail_np["solar_mw"],
        "wind_mw": detail_np["wind_mw"],

        "non_pilotable_total_mw": (detail_np["solar_mw"] + detail_np["wind_mw"]),

        "demande_residuelle_mw": (point_demande["demande_residuelle_mw"]),

        "production_nucleaire_mw": production_mw,
        "production_nucleaire_precedente_mw": production_precedente_mw,

        "variation_mw": variation_mw,
        "sens_variation": sens_variation,
    }


def production_regionale_initiale(regions):
    return {
        region["region_id"]: sum(c["initial_output_mw_at_23_45_previous_day"] for c in region["plants"])
        for region in regions
    }


def equilibrer_region_localement(
    region_id,
    date,
    heure,
    centrales,
    pourcentage,
    etat_precedent,
    prod_reelle,
    productions_sous_minimum,
    productions_sur_maximum
):
    # --------------------------------------------------------
    # 1. Construction des centrales pour ce pas
    # --------------------------------------------------------

    centrales_heure = construire_centrales_heure(
        centrales,
        pourcentage,
        etat_precedent
    )

    # --------------------------------------------------------
    # 2. Demande théorique de la région
    # --------------------------------------------------------

    demande_heure = calculer_demande_heure(
        centrales_heure
    )

    # --------------------------------------------------------
    # 3. Limites réellement accessibles ce pas
    # --------------------------------------------------------

    minimum_regional, maximum_regional = limites_globales(
        centrales_heure
    )

    label_heure = f"{date} {heure}"

    # --------------------------------------------------------
    # 4. CAS : demande supérieure à ce que la région
    #          peut produire actuellement
    # --------------------------------------------------------

    if demande_heure > maximum_regional + EPSILON:

        deficit_residuel = (
            demande_heure
            - maximum_regional
        )

        for centrale in centrales_heure:
            centrale["production"] = centrale["maximum"]

        enregistrer_productions(
            centrales_heure,
            label_heure,
            prod_reelle
        )

        return {
            "region_id": region_id,
            "demande_mw": demande_heure,
            "production_mw": maximum_regional,
            "maximum_regional_mw": maximum_regional,
            "surplus_residuel": 0,
            "deficit_residuel": deficit_residuel,
            "centrales": centrales_heure
        }

    # --------------------------------------------------------
    # 5. CAS : demande inférieure au minimum régional
    # --------------------------------------------------------

    if demande_heure < minimum_regional - EPSILON:

        surplus_residuel = (
            minimum_regional
            - demande_heure
        )

        for centrale in centrales_heure:
            centrale["production"] = centrale["minimum"]

        enregistrer_productions(
            centrales_heure,
            label_heure,
            prod_reelle
        )

        return {
            "region_id": region_id,
            "demande_mw": demande_heure,
            "production_mw": minimum_regional,
            "maximum_regional_mw": maximum_regional,
            "surplus_residuel": surplus_residuel,
            "deficit_residuel": 0,
            "centrales": centrales_heure
        }

    # --------------------------------------------------------
    # 6. CAS NORMAL
    # --------------------------------------------------------

    surplus_a_retirer = sous_minimum(
        centrales_heure,
        label_heure,
        productions_sous_minimum
    )

    deficit_a_repartir = sur_maximum(
        centrales_heure,
        label_heure,
        productions_sur_maximum
    )

    # --------------------------------------------------------
    # 7. Réduction des centrales qui ont été forcées
    #    au-dessus de leur minimum
    # --------------------------------------------------------

    surplus_restant = redistribuer_surplus(
        centrales_heure,
        surplus_a_retirer
    )

    # --------------------------------------------------------
    # 8. Augmentation des centrales qui ont été limitées
    #    par leur maximum
    # --------------------------------------------------------

    deficit_restant = redistribuer_deficit(
        centrales_heure,
        deficit_a_repartir
    )

    # --------------------------------------------------------
    # 9. Production finale
    # --------------------------------------------------------

    production_finale = sum(
        centrale["production"]
        for centrale in centrales_heure
    )

    # --------------------------------------------------------
    # 10. Enregistrement
    # --------------------------------------------------------

    enregistrer_productions(
        centrales_heure,
        label_heure,
        prod_reelle
    )

    # --------------------------------------------------------
    # 11. Résultat régional
    # --------------------------------------------------------

    return {
        "region_id": region_id,
        "demande_mw": demande_heure,
        "production_mw": production_finale,
        "maximum_regional_mw": maximum_regional,
        "surplus_residuel": surplus_restant,
        "deficit_residuel": deficit_restant,
        "centrales": centrales_heure
    }


def equilibrage_local_toutes_regions_nucleaires_predict(
    date_debut=None,
    heure_debut=None,
    date_fin=None,
    heure_fin=None
):
    # ========================================================
    # 1. DONNÉES DE BASE
    # ========================================================

    regions = regions_avec_centrales()

    # Les prévisions contiennent déjà les perturbations actives.
    consommation_par_region = previsions_avec_perturbations()

    demande_residuelle_toutes = (
        demande_moins_non_pilotable_previsions(
            consommation_par_region
        )
    )

    pourcentages, facteur_reserve = (
        pourcentage_repartition_regionale(
            consommation=consommation_par_region,
            demande_residuelle=demande_residuelle_toutes
        )
    )

    non_pilotable_detail = (
        production_non_pilotable_detail_regional()
    )

    minimum_reserve_percent = 8.0

    # ========================================================
    # 2. INDEXATION TEMPORELLE
    # ========================================================
    #
    # Toutes les données sont maintenant accessibles avec :
    #
    #     (date, heure)
    #
    # et non plus avec un index numérique.
    #
    # ========================================================

    consommation_indexee = {
        region_id: indexer_points_par_date_heure(points)
        for region_id, points in consommation_par_region.items()
    }

    demande_residuelle_indexee = {
        region_id: indexer_points_par_date_heure(points)
        for region_id, points in demande_residuelle_toutes.items()
    }

    # ========================================================
    # 3. ÉTAT INITIAL DES CENTRALES
    # ========================================================

    etat_precedent = initialiser_etat()

    # ========================================================
    # 4. STRUCTURES DE RÉSULTATS
    # ========================================================

    prod_reelle = []
    productions_sous_minimum = []
    productions_sur_maximum = []

    resultats_toutes_regions = []
    resultats_routage = []

    echanges_surplus_deficit = []

    energie_non_fournie = []
    energie_a_revendre = []
    situations_degradees = []
    details_regionaux = []

    # ========================================================
    # 5. RÉPARTITION DES RÉGIONS
    # ========================================================

    regions_avec_nucleaire = [
        r
        for r in regions
        if r["region_id"] in pourcentages
    ]

    regions_sans_nucleaire = [
        r
        for r in regions
        if r["region_id"] not in pourcentages
    ]

    # ========================================================
    # 6. RÉGIONS DÉCONNECTÉES
    # ========================================================

    regions_deconnectees = [
        r
        for r in data["parc_nucleaire"]["regions"]
        if not r["connected_to_continental_grid"]
    ]

    ids_deconnectees = {
        normaliser_region(r["id"])
        for r in regions_deconnectees
    }

    # ========================================================
    # 7. MAPPING CENTRALE -> RÉGION
    # ========================================================

    mapping = plant_id_vers_region(
        regions_avec_nucleaire
    )

    capacite_max_region_dict = (
        capacite_max_par_region(
            regions_avec_nucleaire
        )
    )

    # ========================================================
    # 8. PRODUCTION RÉGIONALE PRÉCÉDENTE
    # ========================================================

    production_regionale_precedente = (
        production_regionale_initiale(regions)
    )

    # ========================================================
    # 9. CONSTRUCTION DE LA TIMELINE
    # ========================================================
    #
    # On récupère toutes les clés temporelles disponibles.
    #
    # Exemple :
    #
    # ("2025-07-01", "00:00")
    # ("2025-07-01", "00:30")
    # ("2025-07-01", "01:00")
    #
    # ========================================================

    toutes_les_cles = set()

    for points in demande_residuelle_indexee.values():
        toutes_les_cles.update(points.keys())

    timeline = sorted(toutes_les_cles)

    # ========================================================
    # 10. FILTRAGE DE LA PÉRIODE DEMANDÉE
    # ========================================================

    if all([
        date_debut,
        heure_debut,
        date_fin,
        heure_fin
    ]):

        debut = datetime.strptime(
            f"{date_debut} {heure_debut}",
            "%Y-%m-%d %H:%M"
        )

        fin = datetime.strptime(
            f"{date_fin} {heure_fin}",
            "%Y-%m-%d %H:%M"
        )

        if debut > fin:
            raise ValueError(
                "La date/heure de début doit être "
                "antérieure ou égale à la date/heure de fin."
            )

        timeline = [
            (date, heure)
            for date, heure in timeline
            if debut <= datetime.strptime(
                f"{date} {heure}",
                "%Y-%m-%d %H:%M"
            ) <= fin
        ]

    # ========================================================
    # 11. SIMULATION TEMPORELLE
    # ========================================================

    for date, heure in timeline:

        # ----------------------------------------------------
        # État des centrales au début de cette demi-heure
        # ----------------------------------------------------

        production_debut_heure = dict(
            etat_precedent
        )

        production_courante = dict(
            etat_precedent
        )

        resultats_heure = []

        # ----------------------------------------------------
        # RÉGIONS AVEC NUCLÉAIRE
        # ----------------------------------------------------

        for region in regions_avec_nucleaire:

            region_id = region["region_id"]

            cle = (date, heure)

            # Récupération du pourcentage par date/heure
            pourcentage = (
                pourcentages
                .get(region_id, {})
                .get(cle)
            )

            if pourcentage is None:
                # Aucun point à cette date/heure
                continue

            resultat = equilibrer_region_localement(
                region_id,
                date,
                heure,
                region["plants"],
                pourcentage,
                etat_precedent,
                prod_reelle,
                productions_sous_minimum,
                productions_sur_maximum
            )

            for centrale in resultat["centrales"]:
                production_courante[
                    centrale["plant_id"]
                ] = centrale["production"]

            resultats_heure.append(resultat)

            # ------------------------------------------------
            # Situation dégradée
            # ------------------------------------------------

            situation = detecter_situation_degradee(
                resultat["region_id"],
                f"{date} {heure}",
                resultat["production_mw"],
                resultat["maximum_regional_mw"],
                capacite_max_region_dict[
                    resultat["region_id"]
                ],
                minimum_reserve_percent
            )

            situations_degradees.append(
                situation
            )

        # ----------------------------------------------------
        # RÉGIONS SANS NUCLÉAIRE
        # ----------------------------------------------------

        resultats_sans_nucleaire = (
            resultats_regions_sans_nucleaire(
                regions_sans_nucleaire,
                demande_residuelle_indexee,
                date,
                heure,
                ids_deconnectees
            )
        )

        resultats_heure.extend(
            resultats_sans_nucleaire
        )

        # ----------------------------------------------------
        # ÉCHANGES SURPLUS / DÉFICIT
        # ----------------------------------------------------

        echanges = repartir_surplus_vers_deficits(
            resultats_heure
        )

        echanges_surplus_deficit.extend(
            echanges
        )

        # ----------------------------------------------------
        # ROUTAGE DES DÉFICITS / SURPLUS
        # ----------------------------------------------------

        for resultat in resultats_heure:

            region_id = resultat["region_id"]

            # =================================================
            # DÉFICIT
            # =================================================

            if resultat["deficit_residuel"] > EPSILON:

                gerer_deficit = router_deficit(
                    region_id,
                    resultat["deficit_residuel"],
                    production_courante,
                    facteur_reserve,
                    donnees_centrales_30_min(),
                    mapping,
                    production_debut_heure
                )

                resultats_routage.append(
                    gerer_deficit
                )

                if (
                    gerer_deficit["demande_non_couverte"]
                    > EPSILON
                ):

                    energie_non_fournie.append({
                        "region_id": region_id,
                        "date": date,
                        "heure": heure,
                        "energie_non_fournie_mw":
                            gerer_deficit[
                                "demande_non_couverte"
                            ]
                    })

            # =================================================
            # SURPLUS
            # =================================================

            if resultat["surplus_residuel"] > EPSILON:

                energie_a_revendre.append({
                    "region_id": region_id,
                    "date": date,
                    "heure": heure,
                    "energie_a_revendre_mw":
                        resultat["surplus_residuel"]
                })

            # =================================================
            # DÉTAIL RÉGIONAL
            # =================================================

            detail = construire_detail_regional(
                region_id,
                date,
                heure,
                resultat["production_mw"],
                production_regionale_precedente[
                    region_id
                ],
                consommation_indexee,
                non_pilotable_detail,
                demande_residuelle_indexee
            )

            details_regionaux.append(
                detail
            )

            # Mise à jour de la production précédente
            production_regionale_precedente[
                region_id
            ] = resultat["production_mw"]

        # ----------------------------------------------------
        # FIN DU PAS DE TEMPS
        # ----------------------------------------------------

        etat_precedent = dict(production_courante)

        # ----------------------------------------------------
        # AJOUT DES RÉSULTATS DE CETTE DEMI-HEURE
        # ----------------------------------------------------

        resultats_toutes_regions.extend(resultats_heure)

    # ========================================================
    # 12. VÉRIFICATION DES RAMPES
    # ========================================================

    erreurs_rampes = verifier_rampes(
        prod_reelle
    )

    # ========================================================
    # 13. RETOUR
    # ========================================================

    return {
        "resultats_toutes_regions": resultats_toutes_regions,
        "prod_reelle": prod_reelle,
        "productions_sous_minimum": productions_sous_minimum,
        "productions_sur_maximum": productions_sur_maximum,
        "resultats_routage": resultats_routage,
        "echanges_surplus_deficit": echanges_surplus_deficit,
        "energie_non_fournie": energie_non_fournie,
        "energie_a_revendre": energie_a_revendre,
        "situations_degradees": situations_degradees,
        "details_regionaux": details_regionaux,
        "erreurs_rampes": erreurs_rampes,
    }


def repartition_par_heure(prod_reelle, label_heure_demandee):
    resultats = []
    centrales = donnees_centrales_30_min()

    for entree in prod_reelle:
        if entree["heure"] != label_heure_demandee:
            continue

        centrale = trouver_centrale(entree["plant_id"], centrales)
        puissance_max = centrale["maximum_power_mw"]
        taux_utilisation = (entree["production"] / puissance_max * 100) if puissance_max > 0 else 0

        resultats.append({
            "plant_id": entree["plant_id"],
            "plant_name": centrale["plant_name"],
            "heure": entree["heure"],
            "production_mw": entree["production"],
            "production_demandee_mw": entree["production_demandee"],
            "puissance_maximum_mw": puissance_max,
            "puissance_minimum_mw": centrale["minimum_operating_power_mw"],
            "taux_utilisation_percent": taux_utilisation,
            "minimum_autorise_mw": entree["minimum_autorise"],
            "maximum_autorise_mw": entree["maximum_autorise"],
            "variation_mw": entree["variation_mw"],
        })

    return resultats


def construire_etats_dashboard_predict(resultats):
    details_regionaux = resultats["details_regionaux"]
    energie_non_fournie = resultats["energie_non_fournie"]
    situations_degradees = resultats["situations_degradees"]

    par_cle = {}
    for d in details_regionaux:
        cle = (d["date"], d["heure"])
        par_cle.setdefault(cle, []).append(d)

    energie_non_fournie_par_cle = {}
    for s in energie_non_fournie:
        cle = (s["date"], s["heure"])
        energie_non_fournie_par_cle[cle] = energie_non_fournie_par_cle.get(cle, 0) + s["energie_non_fournie_mw"]

    reserve_par_label = {}
    heures_degradees = set()
    for s in situations_degradees:
        label = s["heure"]
        reserve_par_label[label] = reserve_par_label.get(label, 0) + s["reserve_disponible_mw"]
        if s["situation_degradee"]:
            heures_degradees.add(label)

    etats = []
    for cle in sorted(par_cle.keys()):
        date, heure = cle
        details_du_point = par_cle[cle]
        unmet_demand = energie_non_fournie_par_cle.get(cle, 0)
        label = f"{date} {heure}"

        if unmet_demand > 0:
            status = "insufficient"
        elif label in heures_degradees:
            status = "degraded"
        else:
            status = "normal"

        etats.append({
            "date": date,
            "time": heure,
            "totalConsumptionMw": sum(d["consommation_mw"] for d in details_du_point),
            "nuclearProductionMw": sum(d["production_nucleaire_mw"] for d in details_du_point),
            "solarProductionMw": sum(d["solar_mw"] for d in details_du_point),
            "windProductionMw": sum(d["wind_mw"] for d in details_du_point),
            "unmetDemandMw": unmet_demand,
            "availableReserveMw": reserve_par_label.get(label, 0),
            "status": status
        })

    return etats


def dashboard_predict():
    resultats = equilibrage_local_toutes_regions_nucleaires_predict()
    return construire_etats_dashboard_predict(resultats)
