import pandas as pd
import duckdb
import requests

CSV_PATH_vacances = "etl_analytique/data/raw/vacances.csv"
CSV_PATH_consommation = "etl_analytique/data/raw/consommation.csv"
CSV_PATH_population = "etl_analytique/data/raw/populations-ofgl-regions.csv"
OUTPUT_PATH_vacances = "etl_analytique/data/vacances_propre.csv"
OUTPUT_PATH_consommation = "etl_analytique/data/consommation_propre.csv"
OUTPUT_PATH_population = "etl_analytique/data/population_propre.csv"
# url_pop_regional = "https://tabular-api.data.gouv.fr/api/resources/e869d234-8f63-452c-8320-d9fcb377d23b/"
# url_dpe = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant"
# #https://github.com/etalab/jours-feries-france <== librairie python des Jours fériés France

# response = requests.get(url_vacance_zone)

# if response.status_code == 200:
#     data = response.json()
#     print(data)
# else:
#     print(f"Erreur : {response.status_code}")

df_vacances = pd.read_csv(CSV_PATH_vacances)

# Nettoyage fichier CSV vacances
print("\n")
print("-" * 40)
print("1 : Vérification dtypes et non-null")
print("-" * 40)
df_vacances.info()

print("-" * 40)
print("2 : Vérification si valeurs manquantes")
print("-" * 40)
print(df_vacances.isnull().sum())
valeurs_manquantes = df_vacances.isnull().sum().sum()
print(f"\nTotal valeurs manquantes : {valeurs_manquantes}\n")

print("-" * 40)
print("3 : Vérification et suppression doublons")
print("-" * 40)
nb_lignes_avant = len(df_vacances)
print(f"\nNombre de données : {nb_lignes_avant}")
doublons_count = df_vacances.duplicated().sum()
print(f"\nNombre de doublons : {doublons_count}")
if doublons_count > 0:
    df_vacances = df_vacances.drop_duplicates()
    nb_lignes_apres = len(df_vacances)
    print(f"\nDoublons supprimés, nouveau nombre de données : {nb_lignes_apres}\n")
else : 
    nb_lignes_apres = len(df_vacances)


df_vacances["date"] = pd.to_datetime(df_vacances["date"], format="mixed", errors="coerce")

df_vacances = df_vacances.dropna(subset = ["date"])
date_limite = '2020-01-01'
df_vacances = df_vacances[df_vacances["date"] >= date_limite]
nb_lignes_apres_date = len(df_vacances)

print("-" * 40)
print("4 : Modif format date , suppression des données avant le 01/01/2020 et supression mauvais format date")
print("-" * 40)
lignes_suppr_date = nb_lignes_apres - nb_lignes_apres_date
print(f"\nNombre de lignes supprimées après formattage date : {lignes_suppr_date}")
print(f"\nLe nouveau nombre de lignes est : {nb_lignes_apres_date}\n")


# df = df.dropna()
# print("-" * 40)
# print("5 : Suppression jours sans vacances")
# print("-" * 40)
nb_lignes_vacances = len(df_vacances)
print(f"\nLe nouveau nombre de lignes est : {nb_lignes_vacances}")

df_vacances.to_csv(OUTPUT_PATH_vacances, index=False)
print(f"\nFichier nettoyé : '{OUTPUT_PATH_vacances}'")

#Fin nettoyage et enregistrement fichier vacances





df_consommation = pd.read_csv(CSV_PATH_consommation, sep=";")

# Nettoyage fichier CSV consommation
print("\n")
print("-" * 40)
print("1 : Vérification dtypes et non-null")
print("-" * 40)
df_consommation.info()

print("-" * 40)
print("2 : Vérification si valeurs manquantes")
print("-" * 40)
print(df_consommation.isnull().sum())
valeurs_manquantes = df_consommation.isnull().sum().sum()
print(f"\nTotal valeurs manquantes : {valeurs_manquantes}\n")

print("-" * 40)
print("3 : Vérification et suppression doublons")
print("-" * 40)
nb_lignes_avant = len(df_consommation)
print(f"\nNombre de données : {nb_lignes_avant}")
doublons_count = df_consommation.duplicated().sum()
print(f"\nNombre de doublons : {doublons_count}")
if doublons_count > 0:
    df_consommation = df_consommation.drop_duplicates()
    nb_lignes_apres = len(df_consommation)
    print(f"\nDoublons supprimés, nouveau nombre de données : {nb_lignes_apres}\n")
else : 
    nb_lignes_apres = len(df_consommation)


df_consommation["Date"] = pd.to_datetime(df_consommation["Date"], format="mixed", errors="coerce")

df_consommation = df_consommation.dropna(subset = ["Date"])
date_limite = '2020-01-01'
df_consommation = df_consommation[df_consommation["Date"] >= date_limite]
nb_lignes_apres_date = len(df_consommation)

print("-" * 40)
print("4 : Modif format date , suppression des données avant le 01/01/2020 et supression mauvais format date")
print("-" * 40)
lignes_suppr_date = nb_lignes_apres - nb_lignes_apres_date
print(f"\nNombre de lignes supprimées après formattage date : {lignes_suppr_date}")
print(f"\nLe nouveau nombre de lignes est : {nb_lignes_apres_date}\n")


nb_lignes_consommation = len(df_consommation)
print(f"\nLe nouveau nombre de lignes est : {nb_lignes_consommation}")


# suppression des colonnes inutiles
df_consommation = df_consommation[['Code INSEE région', 'Région','Date', 'Heure','Consommation (MW)', 'Nucléaire (MW)','Eolien (MW)', 'Solaire (MW)']]

df_consommation.to_csv(OUTPUT_PATH_consommation, index=False)
print(f"\nFichier nettoyé : '{OUTPUT_PATH_consommation}'")

#Fin nettoyage et enregistrement fichier consommation




df_population = pd.read_csv(CSV_PATH_population, sep=";")

# Nettoyage fichier CSV population
print("\n")
print("-" * 40)
print("1 : Vérification dtypes et non-null")
print("-" * 40)
df_population.info()

print("-" * 40)
print("2 : Vérification si valeurs manquantes")
print("-" * 40)
print(df_population.isnull().sum())
valeurs_manquantes = df_population.isnull().sum().sum()
print(f"\nTotal valeurs manquantes : {valeurs_manquantes}\n")

print("-" * 40)
print("3 : Vérification et suppression doublons")
print("-" * 40)
nb_lignes_avant = len(df_population)
print(f"\nNombre de données : {nb_lignes_avant}")
doublons_count = df_population.duplicated().sum()
print(f"\nNombre de doublons : {doublons_count}")
if doublons_count > 0:
    df_population = df_population.drop_duplicates()
    nb_lignes_apres = len(df_population)
    print(f"\nDoublons supprimés, nouveau nombre de données : {nb_lignes_apres}\n")
else : 
    nb_lignes_apres = len(df_population)




df_population = df_population.dropna(subset = ["Exercice"])
date_limite = 2020
df_population = df_population[df_population["Exercice"] >= date_limite]
NOMS_A_SUPPRIMER = ["La Réunion", "Martinique", "Guyane", "Guadeloupe"]
nb_lignes_apres_date = len(df_population)
df_population = df_population[~df_population["Région"].isin(NOMS_A_SUPPRIMER)]
print("-" * 40)
print("4 : Modif format date , suppression des données avant le 01/01/2020 et supression mauvais format date")
print("-" * 40)
lignes_suppr_date = nb_lignes_apres - nb_lignes_apres_date
print(f"\nNombre de lignes supprimées après formattage date : {lignes_suppr_date}")
print(f"\nLe nouveau nombre de lignes est : {nb_lignes_apres_date}\n")



nb_lignes_population = len(df_population)
print(f"\nLe nouveau nombre de lignes est : {nb_lignes_population}")

df_population.to_csv(OUTPUT_PATH_population, index=False)
print(f"\nFichier nettoyé : '{OUTPUT_PATH_population}'")

#Fin nettoyage et enregistrement fichier population








#Creation base analytique et table dim_vacances
con = duckdb.connect("base_analytique.duckdb")

con.execute("""
    CREATE OR REPLACE TABLE dim_vacances AS

SELECT
    ROW_NUMBER() OVER (ORDER BY date) AS id_vacances,
    date,
    vacances_zone_a, 
    vacances_zone_b,
    vacances_zone_c    
FROM
read_csv_auto(
        'etl_analytique/data/vacances_propre.csv',
        header=true
    )
""")

nb = con.execute("SELECT COUNT(*) FROM dim_vacances").fetchone()[0]
print(f"\n{nb} lignes importées lors de la génération de la base analytique.")
# fin creation dim_vacances


#Creation dim_temps
con.execute("""
    CREATE OR REPLACE TABLE dim_temps AS

SELECT
    ROW_NUMBER() OVER (ORDER BY date) AS id_temps,
    dv.id_vacances,
    date,
    heure,
    YEAR(date)                      AS year,
    QUARTER(date)                   AS trimestre,
    MONTH(date)                     AS month,
    DAY(date)                       AS day,
    WEEK(date)                      AS week,
    DAYOFWEEK(date)                 AS day_week_number,
    DAYNAME(date)                   AS day_name,
    MONTHNAME(date)                 AS month_name,

    CASE
        WHEN DAYOFWEEK(date) IN (0,6)
        THEN TRUE
        ELSE FALSE
    END                                      AS weekend,

    CASE
        WHEN MONTH(date) = 3 THEN TRUE
        WHEN MONTH(date) = 4 THEN TRUE
        WHEN MONTH(date) = 5 THEN TRUE
        ELSE FALSE
    END                                      AS printemps,
    
    CASE
        WHEN MONTH(date) = 6 THEN TRUE
        WHEN MONTH(date) = 7 THEN TRUE
        WHEN MONTH(date) = 8 THEN TRUE
        ELSE FALSE
    END                                      AS ete,

    CASE
        WHEN MONTH(date) = 9 THEN TRUE
        WHEN MONTH(date) = 10 THEN TRUE
        WHEN MONTH(date) = 11 THEN TRUE
        ELSE FALSE
    END                                      AS automne,

    CASE
        WHEN MONTH(date) = 12 THEN TRUE
        WHEN MONTH(date) = 1 THEN TRUE
        WHEN MONTH(date) = 2 THEN TRUE
        
        ELSE FALSE
    END                                      AS hiver,


FROM dim_vacances dv

CROSS JOIN (
    SELECT CAST(TIMESTAMP '2000-01-01' + INTERVAL '30 minutes' * i AS TIME) AS heure
    FROM generate_series(0, 47) AS t(i)
) h
;
""")
