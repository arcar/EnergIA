from pathlib import Path
import csv
import re
import unicodedata
import duckdb

from extraction_json import charger_donnees
from simu_nationale import EPSILON, enregistrer_productions, verifier_rampes
from metrique_centrale import router_deficit


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "predict_service" / "base_analytique.duckdb"
CSV_PATH = BASE_DIR / "predict_service" / "predictions" / "previsions_1an.csv"

data = charger_donnees()


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
            "max_ramp_up_mw_per_15_min": centrale["max_ramp_up_mw_per_15_min"] * 2,
            "max_ramp_down_mw_per_15_min": centrale["max_ramp_down_mw_per_15_min"] * 2,
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


def demande_moins_non_pilotable_previsions():
    consommation = charger_previsions_consommation()
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



def pourcentage_repartition_regionale():
    regions = regions_avec_centrales()
    demande_residuelle = demande_moins_non_pilotable_previsions()
    minimum_reserve_percent = 8.0
    facteur_reserve = 1 - (minimum_reserve_percent / 100)
    pourcentage_regional = {}

    for region in regions:
        if not region["plants"]:
            continue

        capacite_max_region = sum(c["maximum_power_mw"] for c in region["plants"])
        if capacite_max_region == 0:
            continue
        capacite_dispo_region = capacite_max_region * facteur_reserve

        points_region = demande_residuelle.get(region["region_id"], [])
        pourcentage_regional[region["region_id"]] = [
            point["demande_residuelle_mw"] / capacite_dispo_region
            for point in points_region
        ]

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


def resultats_regions_sans_nucleaire(regions_sans_nucleaire, demande_residuelle_toutes, index, ids_deconnectees):
    resultats = []
    for region in regions_sans_nucleaire:
        region_id = region["region_id"]
        if region_id in ids_deconnectees:
            continue

        points = demande_residuelle_toutes.get(region_id, [])
        if index >= len(points):
            continue

        valeur_demande = points[index]["demande_residuelle_mw"]
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


def construire_detail_regional(region_id, date, heure, index, production_mw, production_precedente_mw, consommation_par_region, non_pilotable_detail, demande_residuelle_toutes):
    variation_mw = production_mw - production_precedente_mw
    if variation_mw > EPSILON:
        sens_variation = "hausse"
    elif variation_mw < -EPSILON:
        sens_variation = "baisse"
    else:
        sens_variation = "stable"

    mois_jour = date[5:]
    cle = (mois_jour, heure)
    detail_np = non_pilotable_detail.get(region_id, {}).get(cle, {"solar_mw": 0, "wind_mw": 0})

    return {
        "region_id": region_id,
        "date": date,
        "heure": heure,
        "consommation_mw": consommation_par_region[region_id][index]["consommation_mw"],
        "solar_mw": detail_np["solar_mw"],
        "wind_mw": detail_np["wind_mw"],
        "non_pilotable_total_mw": detail_np["solar_mw"] + detail_np["wind_mw"],
        "demande_residuelle_mw": demande_residuelle_toutes[region_id][index]["demande_residuelle_mw"],
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


def equilibrer_region_localement(region_id, date, heure, centrales, pourcentage, etat_precedent, prod_reelle, productions_sous_minimum, productions_sur_maximum):
    centrales_heure = construire_centrales_heure(centrales, pourcentage, etat_precedent)
    demande_heure = calculer_demande_heure(centrales_heure)
    minimum_regional, maximum_regional = limites_globales(centrales_heure)

    label_heure = f"{date} {heure}"

    if demande_heure < minimum_regional:
        surplus_residuel = minimum_regional - demande_heure
        for centrale in centrales_heure:
            centrale["production"] = centrale["minimum"]
        enregistrer_productions(centrales_heure, label_heure, prod_reelle, etat_precedent)
        return {
            "region_id": region_id, 
            "demande_mw": demande_heure, 
            "production_mw": minimum_regional,
            "maximum_regional_mw": maximum_regional, 
            "surplus_residuel": surplus_residuel, 
            "deficit_residuel": 0
        }

    if demande_heure > maximum_regional:
        deficit_residuel = demande_heure - maximum_regional
        for centrale in centrales_heure:
            centrale["production"] = centrale["maximum"]
        enregistrer_productions(centrales_heure, label_heure, prod_reelle, etat_precedent)
        return {
            "region_id": region_id, 
            "demande_mw": demande_heure, 
            "production_mw": maximum_regional,
            "maximum_regional_mw": maximum_regional, 
            "surplus_residuel": 0, 
            "deficit_residuel": deficit_residuel
        }

    surplus_a_retirer = sous_minimum(centrales_heure, label_heure, productions_sous_minimum)
    deficit_a_repartir = sur_maximum(centrales_heure, label_heure, productions_sur_maximum)

    surplus_restant = redistribuer_surplus(centrales_heure, surplus_a_retirer)
    deficit_restant = redistribuer_deficit(centrales_heure, deficit_a_repartir)

    enregistrer_productions(centrales_heure, label_heure, prod_reelle, etat_precedent)

    return {
        "region_id": region_id, 
        "demande_mw": demande_heure,
        "production_mw": sum(c["production"] for c in centrales_heure),
        "maximum_regional_mw": maximum_regional,
        "surplus_residuel": surplus_restant, 
        "deficit_residuel": deficit_restant
    }



def equilibrage_local_toutes_regions_nucleaires_predict():
    regions = regions_avec_centrales()
    pourcentages, facteur_reserve = pourcentage_repartition_regionale()
    demande_residuelle_toutes = demande_moins_non_pilotable_previsions()
    consommation_par_region = charger_previsions_consommation()
    non_pilotable_detail = production_non_pilotable_detail_regional()
    minimum_reserve_percent = 8.0

    etat_precedent = initialiser_etat()

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

    regions_avec_nucleaire = [r for r in regions if r["region_id"] in pourcentages]
    regions_sans_nucleaire = [r for r in regions if r["region_id"] not in pourcentages]
    regions_deconnectees = [r for r in data["parc_nucleaire"]["regions"] if not r["connected_to_continental_grid"]]
    ids_deconnectees = {normaliser_region(r["id"]) for r in regions_deconnectees}

    mapping = plant_id_vers_region(regions_avec_nucleaire)
    capacite_max_region_dict = capacite_max_par_region(regions_avec_nucleaire)

    production_regionale_precedente = production_regionale_initiale(regions)

    if regions_avec_nucleaire and regions_avec_nucleaire[0]["region_id"] in demande_residuelle_toutes:
        region_reference = regions_avec_nucleaire[0]["region_id"]
    else:
        region_reference = next(iter(demande_residuelle_toutes))
    timeline = [(p["date"], p["heure"]) for p in demande_residuelle_toutes[region_reference]]

    for index, (date, heure) in enumerate(timeline):
        production_debut_heure = dict(etat_precedent)
        resultats_heure = []

        for region in regions_avec_nucleaire:
            pourcentage_liste = pourcentages[region["region_id"]]
            if index >= len(pourcentage_liste):
                continue

            resultat = equilibrer_region_localement(
                region["region_id"], date, heure, region["plants"], pourcentage_liste[index],
                etat_precedent, prod_reelle, productions_sous_minimum, productions_sur_maximum
            )
            resultats_heure.append(resultat)

            situation = detecter_situation_degradee(
                resultat["region_id"], f"{date} {heure}", resultat["production_mw"],
                resultat["maximum_regional_mw"], capacite_max_region_dict[resultat["region_id"]],
                minimum_reserve_percent
            )
            situations_degradees.append(situation)

        resultats_heure.extend(resultats_regions_sans_nucleaire(regions_sans_nucleaire, demande_residuelle_toutes, index, ids_deconnectees))

        echanges = repartir_surplus_vers_deficits(resultats_heure)
        echanges_surplus_deficit.extend(echanges)

        for resultat in resultats_heure:
            region_id = resultat["region_id"]

            if resultat["deficit_residuel"] > EPSILON:
                gerer_deficit = router_deficit(region_id, resultat["deficit_residuel"], etat_precedent, facteur_reserve, donnees_centrales_30_min(), mapping, production_debut_heure)
                resultats_routage.append(gerer_deficit)

                if gerer_deficit["demande_non_couverte"] > EPSILON:
                    energie_non_fournie.append({
                        "region_id": region_id, "date": date, "heure": heure,
                        "energie_non_fournie_mw": gerer_deficit["demande_non_couverte"]
                    })

            if resultat["surplus_residuel"] > EPSILON:
                energie_a_revendre.append({
                    "region_id": region_id, "date": date, "heure": heure,
                    "energie_a_revendre_mw": resultat["surplus_residuel"]
                })

            detail = construire_detail_regional(
                region_id, date, heure, index, resultat["production_mw"],
                production_regionale_precedente[region_id], consommation_par_region,
                non_pilotable_detail, demande_residuelle_toutes)
            details_regionaux.append(detail)

            production_regionale_precedente[region_id] = resultat["production_mw"]

        resultats_toutes_regions.extend(resultats_heure)

    erreurs_rampes = verifier_rampes(prod_reelle)

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


print(dashboard_predict())