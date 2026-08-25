from calcul_score_central import extract_data, calcul_scores, find_centrale, extract_production, extract_consomation_temporels

from dijkstra.region_service import RegionService
from dijkstra.json_repository import JsonRepository
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
json_file = BASE_DIR / "data" / "parc-nucleaire-prescriptif-france.json"

repository = JsonRepository(str(json_file))

#repository = JsonRepository("data/parc-nucleaire-prescriptif-france.json")
region_service = RegionService(repository)





def get_puissance_disponible(centrale):
    return (centrale["simulation"]["soft_upper_bound_mw"] - centrale["simulation"]["initial_output_mw"])

def get_centrale_disponible(centrale):
    return centrale["simulation"]["available"]

def get_taux_saturation(centrale):
    return centrale["simulation"]["soft_upper_bound_ratio"]

def get_nom_region(centrale):
    return centrale["location"]["region_id"]

def get_central_id(centrale):
    return centrale["id"]

def get_metrique_centrale():
    donnees = extract_data()
    metriques = []

    for centrale in donnees["plants"]:

        metriques.append({
            "puissance_disponible" : get_puissance_disponible(centrale),
            "taux_saturation": get_taux_saturation(centrale),
            "disponible": get_centrale_disponible(centrale),
            "region": get_nom_region(centrale),
            "central_id": get_central_id(centrale)
        })

    metriques.sort(key=lambda x: x["region"])
    return metriques

def get_centrale_regionale(region):
    metriques = get_metrique_centrale()
    centrales_regionale = []
    
    for region_metriques in metriques:
         if (region_metriques["region"].lower() == region.lower()):
            centrales_regionale.append(region_metriques)

    return centrales_regionale

def calcul_demande_residuelle(augmentation, region):
    centrales_regionale = get_centrale_regionale(region)

    puissance_disponible_regional = sum(centrale["puissance_disponible"] for centrale in centrales_regionale)
    demande_residuelle = augmentation - puissance_disponible_regional

    return demande_residuelle, puissance_disponible_regional


def match_central_region():

    donnees_centrale = extract_production()
    donnees_parc_nucleaire = extract_data()

    resultats = []

    for centrales in donnees_centrale["plants"]:

        for centrale_parc_nucleaire in donnees_parc_nucleaire["plants"]:

            if centrales["plant_id"] == centrale_parc_nucleaire["id"]:

                simulation = centrale_parc_nucleaire.get(
                    "simulation",
                    {}
                )

                resultats.append({

                    "region":
                        centrale_parc_nucleaire["location"]["region_id"],

                    "centrale":
                        centrales["plant_id"],

                    "nom":
                        centrale_parc_nucleaire["name"],

                    "initial_output_mw":
                        centrales[
                            "initial_output_mw_at_23_45_previous_day"
                        ],

                    "minimum_operating_power_mw":
                        centrales[
                            "minimum_operating_power_mw"
                        ],

                    "maximum_power_mw":
                        centrales[
                            "maximum_power_mw"
                        ],

                    "max_ramp_up_mw_per_15_min":
                        centrales[
                            "max_ramp_up_mw_per_15_min"
                        ],

                    "max_ramp_down_mw_per_15_min":
                        centrales[
                            "max_ramp_down_mw_per_15_min"
                        ],

                    "soft_upper_bound_mw":
                        simulation.get(
                            "soft_upper_bound_mw",
                            centrales["maximum_power_mw"]
                        ),

                    "initial_dispatchable_margin_mw":
                        simulation.get(
                            "initial_dispatchable_margin_mw",
                            0
                        ),

                    "technical_penalty":
                        simulation.get(
                            "technical_penalty",
                            1.0
                        ),

                    "installed_power_mw":
                        centrale_parc_nucleaire.get(
                            "installed_power_mw",
                            0
                        )
                })

    return resultats

def calcul_prodduction_regional():

    donnees_centrale_regional = match_central_region()

    production_regional_initial = []

    # ============================================================
    # REGROUPEMENT DES CENTRALES PAR REGION
    # ============================================================

    regions = {}

    for centrale in donnees_centrale_regional:

        region = centrale["region"]

        if region not in regions:

            regions[region] = {
                "region": region,
                "production_initial": 0,
                "centrales": []
            }

        # --------------------------------------------------------
        # PRODUCTION REGIONALE
        # --------------------------------------------------------

        regions[region]["production_initial"] += (
            centrale["initial_output_mw"]
        )

        # --------------------------------------------------------
        # AJOUT DE LA CENTRALE
        # --------------------------------------------------------

        regions[region]["centrales"].append({

            "id":
                centrale["centrale"],

            "name":
                centrale["nom"],

            "production_initial":
                centrale["initial_output_mw"],

            "minimum_operating_power_mw":
                centrale["minimum_operating_power_mw"],

            "maximum_power_mw":
                centrale["maximum_power_mw"],

            "soft_upper_bound_mw":
                centrale["soft_upper_bound_mw"],

            "initial_dispatchable_margin_mw":
                centrale[
                    "initial_dispatchable_margin_mw"
                ],

            "max_ramp_up_mw_per_15_min":
                centrale[
                    "max_ramp_up_mw_per_15_min"
                ],

            "max_ramp_down_mw_per_15_min":
                centrale[
                    "max_ramp_down_mw_per_15_min"
                ],

            "technical_penalty":
                centrale["technical_penalty"]
        })

    # ============================================================
    # CONVERSION EN LISTE
    # ============================================================

    production_regional_initial = list(
        regions.values()
    )

    return production_regional_initial



def prod_initiale_a_repartir():

    donnees_centrale_regional_a_repartir = (
        calcul_prodduction_regional()
    )

    donnees_region_a_deduire = (
        extract_consomation_temporels()
    )

    production_regional_initial_a_repartir = []

    # ============================================================
    # INDEX DES REGIONS DU JSON DE CONSOMMATION
    # ============================================================

    regions_json = {
        region["id"]: region
        for region in donnees_region_a_deduire["regions"]
    }

    # ============================================================
    # REGIONS AYANT UNE PRODUCTION
    # ============================================================

    regions_production = set()

    for region_data in donnees_centrale_regional_a_repartir:

        region = region_data["region"]

        production_totale = region_data[
            "production_initial"
        ]

        centrales = region_data["centrales"]

        regions_production.add(region)

        donnees_region = regions_json.get(region)

        # --------------------------------------------------------
        # CONSOMMATION LOCALE
        # --------------------------------------------------------

        if (
            donnees_region
            and donnees_region.get("consumption_mw")
        ):

            consommation_initiale = (
                donnees_region["consumption_mw"][0]
            )

        else:

            consommation_initiale = 0

        # --------------------------------------------------------
        # CONSOMMATION ANNUELLE MOYENNE
        # --------------------------------------------------------

        annual_average_consumption = (

            donnees_region.get(
                "annual_average_consumption_mw_2024",
                0
            )

            if donnees_region

            else 0
        )

        # --------------------------------------------------------
        # PRODUCTION REGIONALE A REPARTIR
        # --------------------------------------------------------

        production_a_repartir = (
            production_totale
            - consommation_initiale
        )

        # ========================================================
        # CENTRALES
        # ========================================================

        centrales_resultat = []

        for centrale in centrales:

            production_centrale = (
                centrale["production_initial"]
            )

            # ----------------------------------------------------
            # PART DE LA CENTRALE
            # ----------------------------------------------------

            if production_totale > 0:

                part_centrale = (
                    production_centrale
                    / production_totale
                )

            else:

                part_centrale = 0

            # ----------------------------------------------------
            # PRODUCTION APRES CONSOMMATION LOCALE
            # ----------------------------------------------------

            production_centrale_a_repartir = (

                production_a_repartir
                * part_centrale
            )

            # ----------------------------------------------------
            # SOFT UPPER BOUND
            # ----------------------------------------------------

            soft_upper_bound = (
                centrale["soft_upper_bound_mw"]
            )

            # ----------------------------------------------------
            # MAXIMUM ENVOYABLE
            # ----------------------------------------------------

            production_max_a_envoyer = min(

                max(
                    production_centrale_a_repartir,
                    0
                ),

                soft_upper_bound
            )

            # ----------------------------------------------------
            # RESULTAT CENTRALE
            # ----------------------------------------------------

            centrales_resultat.append({

                "id":
                    centrale["id"],

                "name":
                    centrale["name"],

                "production_initial":
                    production_centrale,

                "production_initial_a_repartir":
                    round(production_centrale_a_repartir),

                "soft_upper_bound_mw":
                    soft_upper_bound,

                "production_max_a_envoyer":
                    round(production_max_a_envoyer),

                "initial_dispatchable_margin_mw":
                    centrale[
                        "initial_dispatchable_margin_mw"
                    ],

                "max_ramp_up_mw_per_15_min":
                    centrale[
                        "max_ramp_up_mw_per_15_min"
                    ],

                "max_ramp_down_mw_per_15_min":
                    centrale[
                        "max_ramp_down_mw_per_15_min"
                    ],

                "minimum_operating_power_mw":
                    centrale[
                        "minimum_operating_power_mw"
                    ],

                "maximum_power_mw":
                    centrale[
                        "maximum_power_mw"
                    ],

                "technical_penalty":
                    centrale["technical_penalty"]
            })

        # ========================================================
        # RESULTAT REGION
        # ========================================================

        production_regional_initial_a_repartir.append({

            "region":
                region,

            "production_initial":
                production_totale,

            "consommation_locale":
                consommation_initiale,

            "production_initial_a_repartir":
                production_a_repartir,

            "annual_average_consumption_mw_2024":
                annual_average_consumption,

            "centrales":
                centrales_resultat
        })

# ============================================================
# REGIONS SANS PRODUCTION
# ============================================================

    # Lecture du JSON parc nucléaire
    donnees_parc_nucleaire = extract_data()

    # Index des PDL par region_id
    pdl_par_region = {
        pdl["location"]["region_id"]: pdl
        for pdl in donnees_parc_nucleaire.get("PDL", [])
    }


    for region in donnees_region_a_deduire["regions"]:

        region_id = region["id"]

        # --------------------------------------------------------
        # REGION SANS CENTRALE
        # --------------------------------------------------------

        if region_id not in regions_production:

            # ----------------------------------------------------
            # CONSOMMATION INITIALE
            # ----------------------------------------------------

            if region.get("consumption_mw"):

                consommation_initiale = (
                    region["consumption_mw"][0]
                )

            else:

                consommation_initiale = 0

            # ----------------------------------------------------
            # RECHERCHE DU PDL DE LA REGION
            # ----------------------------------------------------

            pdl = pdl_par_region.get(region_id)

            centrales_region = []

            if pdl:

                centrales_region.append({

                    "id":
                        pdl["id"],

                    "name":
                        pdl["name"],

                    "type":
                        "PDL",

                    "production_initial":
                        0,

                    "production_initial_a_repartir":
                        0,

                    "production_max_a_envoyer":
                        0,

                    "soft_upper_bound_mw":
                        0,

                    "initial_dispatchable_margin_mw":
                        0,

                    "max_ramp_up_mw_per_15_min":
                        0,

                    "max_ramp_down_mw_per_15_min":
                        0,

                    "minimum_operating_power_mw":
                        0,

                    "maximum_power_mw":
                        0,

                    "technical_penalty":
                        1.0
                })

            # ----------------------------------------------------
            # RESULTAT REGION
            # ----------------------------------------------------

            production_regional_initial_a_repartir.append({

                "region":
                    region_id,

                "production_initial":
                    0,

                "consommation_locale":
                    consommation_initiale,

                "production_initial_a_repartir":
                    -consommation_initiale,

                "annual_average_consumption_mw_2024":
                    region.get(
                        "annual_average_consumption_mw_2024",
                        0
                    ),

                "centrales":
                    centrales_region
            })
    # ============================================================
    # TRI DES REGIONS
    # ============================================================

    production_regional_initial_a_repartir.sort(

        key=lambda x:
            x["annual_average_consumption_mw_2024"],

        reverse=True
    )

    return production_regional_initial_a_repartir
print(prod_initiale_a_repartir())
    


def repartition_initiale_minuit():
    production_regional_initial_a_repartir = prod_initiale_a_repartir()
    regions_a_fournir = []
    regions_sugar_daddy = []

    for region in production_regional_initial_a_repartir:
        if region["production_initial_a_repartir"]<0:
            regions_a_fournir.append(region)
        else: 
            regions_sugar_daddy.append(region)

    for region in regions_a_fournir:
        result = region_service.compute_routes(region["region"])
        destination = region["centrales"]["id"]

        for source_plant in regions_sugar_daddy:


        candidats  = []
        for destination, route_info in result["routes"].items():

            centrale = find_centrale(extract_data()["plants"], destination)

            if centrale is not None and centrale["location"]["region_name"] == region:
                print("DESTINATION DANS LA REGION :", destination)
                continue

            if destination == source_plant:
                continue

            distance_km = route_info["distance_km"]
            total_loss_percent = route_info["total_loss_percent"]
            max_transfer_mw = route_info["max_transfer_mw"]

            

            

            resultat = calcul_scores(
                source_plant,
                destination,
                distance_km,
                total_loss_percent,
                max_transfer_mw,
                demande_residuelle
            )
            if resultat is not None:
                candidats.append(resultat)

        candidats.sort(key=lambda x: x["score_candidat"])

        repartition_externe = []
        demande_restante = demande_residuelle
        index = 0

        while demande_restante > 0 and index < len(candidats):
            candidat = candidats[index]
            production_affectee = min(
                candidat["puissance_disponible"],
                candidat["max_transfer_mw"],
                demande_restante
            )
            candidat["production_affectee"] = production_affectee 
            repartition_externe.append(candidat)
            demande_restante -= production_affectee
            index += 1
            candidat["production_restante"] = (
                candidat["puissance_disponible"] - production_affectee
            )

def repartition(augmentation, region):
    donnees = extract_data()
    demande_residuelle, puissance_disponible_regional = calcul_demande_residuelle(augmentation, region)
    centrales_regionale = get_centrale_regionale(region)

    for regions in donnees["regions"]:
        if(region == regions["id"]):
            if (regions["connected_to_continental_grid"] == False):
                return {"reponse": "La région n'est pas connecté au réseau national"}
    
    if (demande_residuelle <= 0):
        production_affectee = [centrale["puissance_disponible"] / puissance_disponible_regional * augmentation for centrale in centrales_regionale]
        repartition_locale = []

        for i, centrale in enumerate(centrales_regionale):
            repartition_locale.append({
                "central_id": centrale["central_id"],
                "production_affectee": production_affectee[i],
                "production_restante": (
                    centrale["puissance_disponible"] - production_affectee[i]
                )
            })

        return repartition_locale
    else:
        repartition_locale = []
    
        for centrale in centrales_regionale:
            repartition_locale.append({
                "central_id": centrale["central_id"],
                "production_affectee": centrale["puissance_disponible"],
                "production_restante": 0
                
            })
        
        result = region_service.compute_routes(region)
        source_plant = result["source_plant"]

        donnees = extract_data()
        plant_ids = set(p["id"] for p in donnees["plants"])

        candidats  = []
        for destination, route_info in result["routes"].items():

            centrale = find_centrale(extract_data()["plants"], destination)

            if centrale is not None and centrale["location"]["region_name"] == region:
                print("DESTINATION DANS LA REGION :", destination)
                continue

            if destination == source_plant:
                continue

            distance_km = route_info["distance_km"]
            total_loss_percent = route_info["total_loss_percent"]
            max_transfer_mw = route_info["max_transfer_mw"]

            

            

            resultat = calcul_scores(
                source_plant,
                destination,
                distance_km,
                total_loss_percent,
                max_transfer_mw,
                demande_residuelle
            )
            if resultat is not None:
                candidats.append(resultat)

        candidats.sort(key=lambda x: x["score_candidat"])

        repartition_externe = []
        demande_restante = demande_residuelle
        index = 0

        while demande_restante > 0 and index < len(candidats):
            candidat = candidats[index]
            production_affectee = min(
                candidat["puissance_disponible"],
                candidat["max_transfer_mw"],
                demande_restante
            )
            candidat["production_affectee"] = production_affectee 
            repartition_externe.append(candidat)
            demande_restante -= production_affectee
            index += 1
            candidat["production_restante"] = (
                candidat["puissance_disponible"] - production_affectee
            )

        return {
            "repartition_locale" : repartition_locale,
            "repartition_externe" : repartition_externe,
            "demande_non_couverte" : demande_restante
        }

def consomation_regionale():
    donnees_regionale = extract_consomation_temporels
    for region in donnees_regionale["regions"]:
        for consomation_quart in region["consumption_mw"]:
            return {
                "region_id" : region["id"],
                "consomation_quart": consomation_quart
            }

def match_central_region():
    donnees_centrale = extract_production()
    donnees_parc_nucleaire = extract_data()

    for centrales in donnees_centrale["plants"]:
        for centrale_parc_nucleaire in donnees_parc_nucleaire["plants"]:
            if (centrales["plant_id"] == centrale_parc_nucleaire["id"]):
                return {
                    "region": centrale_parc_nucleaire["location"]["region_id"],
                    "centrale": centrales["plant_id"]
                }


    