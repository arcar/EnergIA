from calcul_score_central import extract_data


# Réserve minimale souhaitée du parc nucléaire
RESERVE_MIN_PERCENT = 15


def get_capacite_totale_parc():
    donnees = extract_data()

    capacite_totale = 0

    for centrale in donnees["plants"]:
        capacite_totale += centrale["simulation"]["soft_upper_bound_mw"]

    return capacite_totale

def get_capacite_disponible_parc():
    donnees = extract_data()

    capacite_disponible = 0

    for centrale in donnees["plants"]:
        capacite_disponible += (
            centrale["simulation"]["soft_upper_bound_mw"]
            - centrale["simulation"]["initial_output_mw"]
        )

    return capacite_disponible

def get_reserve_percent():
    capacite_totale = get_capacite_totale_parc()
    capacite_disponible = get_capacite_disponible_parc()

    if capacite_totale == 0:
        return 0

    return (capacite_disponible / capacite_totale) * 100

#Vérifier l'état de la réserve

def verifier_reserve():
    capacite_totale = get_capacite_totale_parc()
    capacite_disponible = get_capacite_disponible_parc()
    reserve_actuelle = get_reserve_percent()

    if reserve_actuelle >= RESERVE_MIN_PERCENT:
        etat = "normal"
    else:
        etat = "degrade"

    return {
        "capacite_totale_mw": capacite_totale,
        "capacite_disponible_mw": capacite_disponible,
        "reserve_percent": reserve_actuelle,
        "reserve_min_percent": RESERVE_MIN_PERCENT,
        "etat": etat
    }

#--------------------------------------
# TEST console
#--------------------------------------

print(verifier_reserve())