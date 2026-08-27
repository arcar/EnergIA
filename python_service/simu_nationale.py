import os
import json
import numpy as np


# ============================================================
# CONFIGURATION DES FICHIERS
# ============================================================

PARENT = os.path.dirname(os.path.abspath(__file__))

PARC_NUCLEAIRE_DATA = os.path.join(
    PARENT,
    "data",
    "parc-nucleaire-prescriptif-france.json"
)

PARAMETRES_TEMPORELS_NUCLEAIRE_DATA = os.path.join(
    PARENT,
    "data",
    "energia-parametres-temporels-nucleaire.json"
)

REFERENCE_CONSOMMATION_DATA = os.path.join(
    PARENT,
    "data",
    "energia-journee-reference-consommation.json"
)

PARC_NON_PILOTABLE_DATA = os.path.join(
    PARENT,
    "data",
    "energia-production-non-pilotable.json"
)

EPSILON = 0.000001


# ============================================================
# CHARGEMENT
# ============================================================

def charger_json(chemin):
    with open(chemin, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def charger_donnees():
    return {
        "parc_nucleaire": charger_json(PARC_NUCLEAIRE_DATA),
        "params_temporels": charger_json(
            PARAMETRES_TEMPORELS_NUCLEAIRE_DATA
        ),
        "consommation": charger_json(
            REFERENCE_CONSOMMATION_DATA
        ),
        "non_pilotable": charger_json(
            PARC_NON_PILOTABLE_DATA
        ),
    }


# ============================================================
# CALCUL DE LA CAPACITE NUCLEAIRE
# ============================================================

def calculer_capacites_nucleaires(params_temporels):

    production_maximale = sum(
        centrale["maximum_power_mw"]
        for centrale in params_temporels["plants"]
    )

    production_minimale = sum(
        centrale["minimum_operating_power_mw"]
        for centrale in params_temporels["plants"]
    )

    return production_minimale, production_maximale


# ============================================================
# CALCUL DE LA DEMANDE RESIDUELLE
# ============================================================

def calculer_demande_residuelle(consommation, non_pilotable):

    consommation_nationale = np.array(
        consommation["national_total_consumption_mw"]
    )

    production_non_pilotable = np.array(
        non_pilotable[
            "national_total_production_mw"
        ]["solar_plus_wind"]
    )

    return (
        consommation_nationale - production_non_pilotable
    ).tolist()


def calculer_pourcentages_production(
    demande_residuelle,
    production_maximale_nucleaire
):

    return (
        np.array(demande_residuelle)
        / production_maximale_nucleaire
    ).tolist()


# ============================================================
# ETAT INITIAL
# ============================================================

def initialiser_etat(params_temporels):

    return {
        centrale["plant_id"]:
            centrale["initial_output_mw_at_23_45_previous_day"]
        for centrale in params_temporels["plants"]
    }


# ============================================================
# CALCUL D'UNE CENTRALE POUR UN QUART D'HEURE
# ============================================================

def calculer_centrale_heure(
    centrale,
    pourcentage,
    etat_precedent
):

    plant_id = centrale["plant_id"]

    production_demandee = (
        centrale["maximum_power_mw"]
        * pourcentage
    )

    production_precedente = etat_precedent[plant_id]

    # --------------------------------------------------------
    # LIMITES TECHNIQUES
    # --------------------------------------------------------

    minimum_technique = (
        centrale["minimum_operating_power_mw"]
    )

    maximum_technique = (
        centrale["maximum_power_mw"]
    )

    # --------------------------------------------------------
    # LIMITES TEMPORELLES
    # --------------------------------------------------------

    minimum_temporel = (
        production_precedente
        - centrale["max_ramp_down_mw_per_15_min"]
    )

    maximum_temporel = (
        production_precedente
        + centrale["max_ramp_up_mw_per_15_min"]
    )

    # --------------------------------------------------------
    # LIMITES EFFECTIVEMENT APPLICABLES
    # --------------------------------------------------------

    minimum_autorise = max(
        minimum_technique,
        minimum_temporel
    )

    maximum_autorise = min(
        maximum_technique,
        maximum_temporel
    )

    return {
        "plant_id": plant_id,
        "production": production_demandee,
        "production_demandee": production_demandee,
        "production_precedente": production_precedente,
        "minimum": minimum_autorise,
        "maximum": maximum_autorise,
        "minimum_technique": minimum_technique,
        "maximum_technique": maximum_technique,
        "rampe_montee": centrale[
            "max_ramp_up_mw_per_15_min"
        ],
        "rampe_descente": centrale[
            "max_ramp_down_mw_per_15_min"
        ],
    }


# ============================================================
# CONSTRUCTION DES CENTRALES POUR UNE HEURE
# ============================================================

def construire_centrales_heure(
    centrales,
    pourcentage,
    etat_precedent
):

    centrales_heure = []

    for centrale in centrales:

        centrale_heure = calculer_centrale_heure(
            centrale,
            pourcentage,
            etat_precedent
        )

        centrales_heure.append(centrale_heure)

    return centrales_heure


# ============================================================
# DEMANDE TOTALE
# ============================================================

def calculer_demande_heure(centrales_heure):

    return sum(
        centrale["production_demandee"]
        for centrale in centrales_heure
    )


# ============================================================
# LIMITES GLOBALES
# ============================================================

def calculer_limites_globales(centrales_heure):

    production_minimale = sum(
        centrale["minimum"]
        for centrale in centrales_heure
    )

    production_maximale = sum(
        centrale["maximum"]
        for centrale in centrales_heure
    )

    return production_minimale, production_maximale


# ============================================================
# ENREGISTREMENT
# ============================================================

def enregistrer_productions(
    centrales,
    heure,
    prod_reelle,
    etat_precedent
):

    for centrale in centrales:

        prod_reelle.append({
            "plant_id": centrale["plant_id"],
            "heure": heure,
            "production": centrale["production"],
            "production_demandee": centrale["production_demandee"],
            "production_precedente": centrale["production_precedente"],
            "variation_mw": (
                centrale["production"]
                - centrale["production_precedente"]
            ),
            "minimum_autorise": centrale["minimum"],
            "maximum_autorise": centrale["maximum"],
            "production_minimum_technique": (
                centrale["minimum_technique"]
            ),
            "production_maximum_technique": (
                centrale["maximum_technique"]
            ),
            "rampe_montee_maximale": (
                centrale["rampe_montee"]
            ),
            "rampe_descente_maximale": (
                centrale["rampe_descente"]
            ),
        })

        etat_precedent[
            centrale["plant_id"]
        ] = centrale["production"]


# ============================================================
# CENTRALES SOUS LE MINIMUM
# ============================================================

def ajuster_sous_minimum(
    centrales_heure,
    heure,
    productions_sous_minimum
):

    surplus_a_retirer = 0

    for centrale in centrales_heure:

        if centrale["production"] < centrale["minimum"]:

            surplus = (
                centrale["minimum"]
                - centrale["production"]
            )

            surplus_a_retirer += surplus

            productions_sous_minimum.append({
                "plant_id": centrale["plant_id"],
                "heure": heure,
                "production_demandee": (
                    centrale["production_demandee"]
                ),
                "production_minimum": (
                    centrale["minimum"]
                ),
                "surplus": surplus
            })

            centrale["production"] = (
                centrale["minimum"]
            )

    return surplus_a_retirer


# ============================================================
# CENTRALES AU-DESSUS DU MAXIMUM
# ============================================================

def ajuster_sur_maximum(
    centrales_heure,
    heure,
    productions_sur_maximum
):

    deficit_a_repartir = 0

    for centrale in centrales_heure:

        if centrale["production"] > centrale["maximum"]:

            deficit = (
                centrale["production"]
                - centrale["maximum"]
            )

            deficit_a_repartir += deficit

            productions_sur_maximum.append({
                "plant_id": centrale["plant_id"],
                "heure": heure,
                "production_demandee": (
                    centrale["production_demandee"]
                ),
                "production_maximum": (
                    centrale["maximum"]
                ),
                "deficit": deficit
            })

            centrale["production"] = (
                centrale["maximum"]
            )

    return deficit_a_repartir


# ============================================================
# REDISTRIBUTION GENERIQUE
# ============================================================

def redistribuer(
    centrales_heure,
    quantite,
    borne,
    operation
):

    while quantite > EPSILON:

        centrales_disponibles = [
            centrale
            for centrale in centrales_heure
            if borne(centrale)
        ]

        if not centrales_disponibles:
            break

        variation_par_centrale = (
            quantite
            / len(centrales_disponibles)
        )

        quantite_restante = 0

        for centrale in centrales_disponibles:

            variation, reste = operation(
                centrale,
                variation_par_centrale
            )

            centrale["production"] += variation

            quantite_restante += reste

        quantite = quantite_restante

    return quantite


# ============================================================
# REDISTRIBUTION DU SURPLUS
# ============================================================

def redistribuer_surplus(
    centrales_heure,
    surplus_a_retirer
):

    return redistribuer(
        centrales_heure,

        surplus_a_retirer,

        lambda centrale:
            centrale["production"]
            > centrale["minimum"] + EPSILON,

        lambda centrale, reduction_demandee: (
            (
                -min(
                    reduction_demandee,
                    centrale["production"]
                    - centrale["minimum"]
                )
            ),
            (
                reduction_demandee
                - min(
                    reduction_demandee,
                    centrale["production"]
                    - centrale["minimum"]
                )
            )
        )
    )


# ============================================================
# REDISTRIBUTION DU DEFICIT
# ============================================================

def redistribuer_deficit(
    centrales_heure,
    deficit_a_repartir
):

    return redistribuer(
        centrales_heure,

        deficit_a_repartir,

        lambda centrale:
            centrale["production"]
            < centrale["maximum"] - EPSILON,

        lambda centrale, augmentation_demandee: (
            (
                min(
                    augmentation_demandee,
                    centrale["maximum"]
                    - centrale["production"]
                )
            ),
            (
                augmentation_demandee
                - min(
                    augmentation_demandee,
                    centrale["maximum"]
                    - centrale["production"]
                )
            )
        )
    )


# ============================================================
# ENERGIE A REVENDRE
# ============================================================

def enregistrer_energie_a_revendre(
    energie_a_revendre,
    heure,
    demande_heure,
    production_mw,
    energie_mw
):

    energie_a_revendre.append({
        "heure": heure,
        "demande_mw": demande_heure,
        "production_mw": production_mw,
        "energie_a_revendre_mw": energie_mw
    })


# ============================================================
# ENERGIE NON FOURNIE
# ============================================================

def enregistrer_energie_non_fournie(
    energie_non_fournie,
    heure,
    demande_heure,
    production_mw,
    energie_mw
):

    energie_non_fournie.append({
        "heure": heure,
        "demande_mw": demande_heure,
        "production_mw": production_mw,
        "energie_non_fournie_mw": energie_mw
    })


# ============================================================
# TRAITEMENT D'UNE HEURE
# ============================================================

def traiter_heure(
    heure,
    pourcentage,
    centrales,
    etat_precedent,
    prod_reelle,
    productions_sous_minimum,
    productions_sur_maximum,
    energie_a_revendre,
    energie_non_fournie
):

    # --------------------------------------------------------
    # CONSTRUCTION DE L'ETAT DES CENTRALES
    # --------------------------------------------------------

    centrales_heure = construire_centrales_heure(
        centrales,
        pourcentage,
        etat_precedent
    )

    demande_heure = calculer_demande_heure(
        centrales_heure
    )

    production_minimale_totale, production_maximale_totale = (
        calculer_limites_globales(centrales_heure)
    )

    # ========================================================
    # CAS 1 : DEMANDE INFERIEURE AU MINIMUM
    # ========================================================

    if demande_heure < production_minimale_totale:

        energie_mw = (
            production_minimale_totale
            - demande_heure
        )

        for centrale in centrales_heure:

            if centrale["production"] < centrale["minimum"]:

                productions_sous_minimum.append({
                    "plant_id": centrale["plant_id"],
                    "heure": heure,
                    "production_demandee": (
                        centrale["production_demandee"]
                    ),
                    "production_minimum": (
                        centrale["minimum"]
                    ),
                    "surplus": (
                        centrale["minimum"]
                        - centrale["production"]
                    )
                })

            centrale["production"] = (
                centrale["minimum"]
            )

        enregistrer_energie_a_revendre(
            energie_a_revendre,
            heure,
            demande_heure,
            production_minimale_totale,
            energie_mw
        )

        enregistrer_productions(
            centrales_heure,
            heure,
            prod_reelle,
            etat_precedent
        )

        return

    # ========================================================
    # CAS 2 : DEMANDE SUPERIEURE AU MAXIMUM
    # ========================================================

    if demande_heure > production_maximale_totale:

        energie_mw = (
            demande_heure
            - production_maximale_totale
        )

        for centrale in centrales_heure:

            if centrale["production"] > centrale["maximum"]:

                productions_sur_maximum.append({
                    "plant_id": centrale["plant_id"],
                    "heure": heure,
                    "production_demandee": (
                        centrale["production_demandee"]
                    ),
                    "production_maximum": (
                        centrale["maximum"]
                    ),
                    "deficit": (
                        centrale["production"]
                        - centrale["maximum"]
                    )
                })

            centrale["production"] = (
                centrale["maximum"]
            )

        enregistrer_energie_non_fournie(
            energie_non_fournie,
            heure,
            demande_heure,
            production_maximale_totale,
            energie_mw
        )

        enregistrer_productions(
            centrales_heure,
            heure,
            prod_reelle,
            etat_precedent
        )

        return

    # ========================================================
    # CAS NORMAL
    # ========================================================

    surplus_a_retirer = ajuster_sous_minimum(
        centrales_heure,
        heure,
        productions_sous_minimum
    )

    deficit_a_repartir = ajuster_sur_maximum(
        centrales_heure,
        heure,
        productions_sur_maximum
    )

    # --------------------------------------------------------
    # REDISTRIBUTION DU SURPLUS
    # --------------------------------------------------------

    surplus_restant = redistribuer_surplus(
        centrales_heure,
        surplus_a_retirer
    )

    if surplus_restant > EPSILON:

        enregistrer_energie_a_revendre(
            energie_a_revendre,
            heure,
            demande_heure,
            sum(
                centrale["production"]
                for centrale in centrales_heure
            ),
            surplus_restant
        )

    # --------------------------------------------------------
    # REDISTRIBUTION DU DEFICIT
    # --------------------------------------------------------

    deficit_restant = redistribuer_deficit(
        centrales_heure,
        deficit_a_repartir
    )

    if deficit_restant > EPSILON:

        enregistrer_energie_non_fournie(
            energie_non_fournie,
            heure,
            demande_heure,
            sum(
                centrale["production"]
                for centrale in centrales_heure
            ),
            deficit_restant
        )

    # --------------------------------------------------------
    # ENREGISTREMENT FINAL
    # --------------------------------------------------------

    enregistrer_productions(
        centrales_heure,
        heure,
        prod_reelle,
        etat_precedent
    )


# ============================================================
# VERIFICATION DES RAMPES
# ============================================================

def verifier_rampes(prod_reelle):

    erreurs_rampes = []

    for production in prod_reelle:

        variation = production["variation_mw"]

        if (
            variation > production["rampe_montee_maximale"] + EPSILON
        ):

            erreurs_rampes.append({
                "plant_id": production["plant_id"],
                "heure": production["heure"],
                "type": "montee_trop_rapide",
                "variation_mw": variation,
                "limite_mw": (
                    production[
                        "rampe_montee_maximale"
                    ]
                )
            })

        if (
            variation < -production["rampe_descente_maximale"] - EPSILON
        ):

            erreurs_rampes.append({
                "plant_id": production["plant_id"],
                "heure": production["heure"],
                "type": "descente_trop_rapide",
                "variation_mw": variation,
                "limite_mw": (
                    production[
                        "rampe_descente_maximale"
                    ]
                )
            })

    return erreurs_rampes


# ============================================================
# AFFICHAGE
# ============================================================

def afficher_resultats(
    prod_reelle,
    productions_sous_minimum,
    productions_sur_maximum,
    energie_a_revendree,
    energie_non_fournie,
    erreurs_rampes
):

    print(
        "NOMBRE D'ERREURS DE RAMPE :",
        len(erreurs_rampes)
    )

    print(
        "ERREURS DE RAMPE :",
        erreurs_rampes
    )

    print(
        "NOMBRE DE PRODUCTIONS REELLES :",
        len(prod_reelle)
    )

    print(
        "NOMBRE DE PRODUCTIONS SOUS MINIMUM :",
        len(productions_sous_minimum)
    )

    print(
        "NOMBRE DE PRODUCTIONS SUR MAXIMUM :",
        len(productions_sur_maximum)
    )

    print(
        "NOMBRE D'HEURES AVEC ENERGIE A REVENDRE :",
        len(energie_a_revendree)
    )

    print(
        "NOMBRE D'HEURES AVEC ENERGIE NON FOURNIE :",
        len(energie_non_fournie)
    )

    print("\nPRODUCTIONS RÉELLES :")
    print(prod_reelle[:40])

    print("\nENERGIE A REVENDRE :")
    print(energie_a_revendree)

    print("\nENERGIE NON FOURNIE :")
    print(energie_non_fournie)


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    # --------------------------------------------------------
    # CHARGEMENT
    # --------------------------------------------------------

    donnees = charger_donnees()

    params_temporels = donnees["params_temporels"]
    consommation = donnees["consommation"]
    non_pilotable = donnees["non_pilotable"]

    # --------------------------------------------------------
    # CAPACITE NUCLEAIRE
    # --------------------------------------------------------

    min_prod_france, prod_nucleaire_france = (calculer_capacites_nucleaires(params_temporels))

    # --------------------------------------------------------
    # DEMANDE RESIDUELLE
    # --------------------------------------------------------

    demande_residuelle = calculer_demande_residuelle(
        consommation,
        non_pilotable
    )

    pourc_prod = calculer_pourcentages_production(
        demande_residuelle,
        prod_nucleaire_france
    )

    # --------------------------------------------------------
    # RESULTATS
    # --------------------------------------------------------

    prod_reelle = []
    productions_sous_minimum = []
    productions_sur_maximum = []
    energie_a_revendre = []
    energie_non_fournie = []

    # --------------------------------------------------------
    # ETAT INITIAL
    # --------------------------------------------------------

    etat_precedent = initialiser_etat(
        params_temporels
    )

    # --------------------------------------------------------
    # TRAITEMENT
    # --------------------------------------------------------

    for heure, pourcentage in zip(
        non_pilotable["timestamps"],
        pourc_prod
    ):

        traiter_heure(
            heure=heure,
            pourcentage=pourcentage,
            centrales=params_temporels["plants"],
            etat_precedent=etat_precedent,
            prod_reelle=prod_reelle,
            productions_sous_minimum=productions_sous_minimum,
            productions_sur_maximum=productions_sur_maximum,
            energie_a_revendre=energie_a_revendre,
            energie_non_fournie=energie_non_fournie
        )

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    erreurs_rampes = verifier_rampes(
        prod_reelle
    )

    # --------------------------------------------------------
    # AFFICHAGE
    # --------------------------------------------------------

    afficher_resultats(
        prod_reelle,
        productions_sous_minimum,
        productions_sur_maximum,
        energie_a_revendre,
        energie_non_fournie,
        erreurs_rampes
    )


# ============================================================
# POINT D'ENTREE
# ============================================================

if __name__ == "__main__":
    main()