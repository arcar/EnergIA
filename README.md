# EnergIA
## Présentation du projet
Objectif du projet : développer la première version d'EnergIA, une plateforme d’aide à la décision destinée au pilotage d’un parc nucléaire

Notre ESN a pour projet de développer, pour un commanditaire, un moteur prescriptif d'aide à la décision pour le pilotage d'un parc nucléaire. Ce moteur doit recommander la répartition optimale d'un besoin de production entre les centrales selon leur capacité, leur saturation et la topologie du réseau. 
L'objectif est de proposer une première version d'EnergIA en se basant sur un graphe simplifié du réseau électrique français et de l'algorithme Dijkstra.


# Prérequis
Pour ce projet, les outils suivants doivent être installés :

* Docker Desktop
* Node.js
* FastAPI
* Git
* Dijkstra


# Installation
## Cloner le dépôt
Le projet est disponible via le lien suivant : https://github.com/arcar/EnergIA

```bash
git clone https://github.com/arcar/EnergIA.git
```


# Configuration
Créer un fichier .env dans le dossier node_gateway contenant :
```
PYTHON_SERVICE_URL=http://python_service:8000
ASSISTANT_URL = http://assistant:3002
```

Créer un fichier .env dans le dossier assistant contenant :
```
PYTHON_SERVICE_URL=http://python_service:8000
OLLAMA_URL=http://ollama:11434
GATEWAY_URL=http://node_gateway:3000
```

Créer un fichier .env dans le dossier python_service contenant :
```
NODE_GATEWAY_URL=http://node_gateway:3000
```


# Lancement de l’application
Ouvrir docker desktop.

Depuis la racine du projet :

```bash
docker compose up -d
```

Cela va permettre de démarrer les conteneurs présents dans le docker compose.


# Exécution des tests
Des tests unitaires ont été réalisés avec **pytest** afin de vérifier le bon fonctionnement du module `metrique_centrale.py`.

Les tests couvrent notamment :

* le calcul de la puissance disponible d'une centrale,
* la vérification de sa disponibilité,
* le calcul du taux de saturation,
* l'identification de la région et de l'identifiant d'une centrale,
* la récupération des centrales d'une région,
* le calcul de la demande résiduelle,
* la répartition de la demande lorsque la puissance disponible est suffisante localement,
* la répartition externe lorsque les capacités locales sont insuffisantes.

**Résultat : 9 tests exécutés, 9 tests réussis.**


# Routes disponibles

## Routes appelées par le MCP via Ollama : 

```
GET http://localhost:3000/assistant/assistant

Params:
name : request
value : question posée en language naturel

La réponse fournie fera appel aux routes:

    - GET_PLANTS : Pour récupèrer toutes les centrales présentes en France.
    - GET_PROD_NATIONALE_HEURE : Pour récupèrer la repartition de la production nationale à une heure donnée.
    - GET_CONSO_REGION_HEURE : Pour récupèrer la consommation demandée d'une région à une heure donnée.
    - GET_PERTURBATION : Simule une perturbation pour une région et l'applique sur la repartition de la production nationale (augmentation ou   diminution de consommation sur une période donnée).
    - UNKNOWN pour renvoyer : "Je n'ai pas les informations à ma disposition pour vous répondre"
```


---
## Routes disponibles depuis la Gateway : http://localhost:3000



### Obtenir toutes les centrales

```
GET /plants
```

***
### Obtenir toutes les informations des régions

```
GET /plants/regions
```

---

### Obtenir toutes les informations de consommation et production pour la France

```
GET /dashboard
```

---

### Obtenir repartition de la production à une heure donnée

```
POST /repartition_heure 
```

Body :

```json
{
    "heure":"21:00"
}
```
---
### Obtenir la répartition de la production de toutes les centrales sur une journée, quart d'heure par quart d'heure

```
GET /repartition/regions
```


## Routes disponibles depuis python-service et non connecté à la Gateway : http://localhost:8000

### Obtenir les informations d'une région donnée

```
GET /routes/{region_id}
```

---

### Obtenir tous les chemins de la première centrale de la région vers toutes les autres

```
GET /regions/routes/(region_id)
```

---


# Format des requêtes
Les requêtes sont formulées en params pour obtenir les routes pour une région et pour le reste en JSON.


# Format des réponses
Les réponses sont également formulées en JSON.


# Fonctionnement du moteur prescriptif
Le moteur prescriptif va, dans un premier temps, vérifier si la puissance disponible au sein de la région couvre la demande d'augmentation en électricité. 
Si celle-ci est suffisante, la puissance demandée est répartie selon les capacités de chaque centrales jusqu'à atteindre un taux de saturation de 95% (comme indiqué dans le fichier JSON fourni : soft_upper_bound_ratio : 0.95).

Si la puissance disponible au sein de la région n'est pas suffisante, le moteur recherche des centrales dans les régions voisines. 
Pour cela, le moteur calcule le plus court chemin entre la région demandeuse et les autres centrales à l'aide de l'algorithme de Dijkstra. Puis, il attribue un score à chaque centrale en fonction de la distance qui la sépare de la région, des pertes énergétique, de la puissance disponible et du niveau de saturation. Les centrales sont ensuite classée par ordre de priorité.
La puissance demandée est alors répartie selon les capacités de chaque centrales jusqu'à atteindre un taux de saturation de 95%.


# Formule ou règles utilisée(s) pour classer les centrales
## Règle 1
Les centrales locales sont examinées en priorité.

## Règle 2
Si la puissance disponible localement n'est pas suffisante le calcul suivant est appliqué pour classer les centrales : 

```
distance_km * distance_weight + loss_percent * loss_weight + pow(final_load_ratio, 4) * saturation_weight + technical_penalty * technical_penalty_weight + regional_priority_bonus_if_local
```

Des coefficients de pondérations sont ainsi appliqués afin de prioriser les centrales : 
*   "distance_weight": 1.0,
*   "loss_weight": 45.0,
*   "saturation_weight": 900.0,
*   "technical_penalty_weight": 200.0

## Règle 3
Si la puissance disponible est inférieure à la demande d'augmentation, une répartition est effectuée avec toutes les centrales et un message calculant la part non couverte apparait à la fin de la réponse.

## Règle 4
Si il est impossible de satisfaire la demande d'augmentation même partiellement, un message "Impossible d'effectuer la simulation" apparait.


# Règles de montée et de descente en puissance des centrales
Les centrales respectent des limites de descente et montée en puissance. Si la puissance demandée est supérieure à ces limites, la centrale augmente ou diminue sa production au maximum de la limite puis une redistribustion l'excédent est réalisée sur les autres centrales.

# Format des données temporelles attendues
Les données doivent être fournies au format HH:mm. Elles correspondent à des pas de 15min (ex: 12:00, 12:15, 12:30,....).

# Calcul des états successifs
Pour chaque quart d’heure, le moteur récupère la consommation de chaque région, détermine la production nucléaire nécessaire et 
répartit cette production entre les centrales en respectant les puissances minimales et maximales de chaque centrale et leurs vitesses de montée et de descente en puissance.
Puis, il conserve l’état obtenu pour le quart d’heure suivant et relance une répartition.

# Calcul de la demande résiduelle
La demande résiduelle correspond à la demande de production nucléaire. À chaque pas de temps de 15 minutes, la demande résiduelle est calculée selon la formule : 
```
Demande résiduelle = Consommation - Production_solaire - Production_eolienne
```
Elle peut être régionale ou nationale.

# Fonctionnement de la réserve minimale
Le moteur conserve une réserve minimale de capacité disponible sur le parc nucléaire. Elle permet aux centrales de garder une marge de fonctionnement. Cette marge a été fixée à 8%. Ainsi, une centrale pourra produire au maximum 92% de sa capacité maximum.
Si ce seuil est atteint la centrale sera identifiée comme étant en situation dégradée.

# Format utilisé pour définir une perturbation de consommation
Pour définir une perturbation, le format suivant a été défini : 
```json
{
  "regionId": "occitanie",
  "start": "17:30",
  "end": "21:00",
  "deltaMw": 850
}
```

# Gestion des validations, logs et erreurs de simulation
Une amélioration de l'API de simulation a été réalisée afin de rendre les échanges plus fiables et plus compréhensibles.

## Validations ajoutées
- Vérification que la région demandée existe avant de lancer une simulation.
- Vérification que l'augmentation de consommation est valide (valeur strictement supérieure à 0 MW).
- Gestion des demandes impossibles lorsque la puissance disponible des centrales locales est insuffisante.

## Gestion des erreurs
- Mise en place de réponses d'erreurs structurées avec un statut, un message explicite et le détail de l'erreur.
- Retour de messages compréhensibles pour faciliter le diagnostic côté utilisateur ou frontend.
- Gestion des erreurs de communication entre la gateway Express et le service FastAPI.

## Ajout des logs
Des journaux ont été ajoutés dans le service de simulation afin de suivre les différentes étapes du traitement :
- Début d'une simulation avec la région et l'augmentation demandée.
- Chargement des données des centrales.
- Calcul des métriques des centrales.
- Nombre de centrales disponibles dans la région demandée.
- Calcul de la demande résiduelle.
- Fin de la répartition de puissance.

## Demander les logs en cas de non affichage après compose up
```
docker compose logs -f NOM_DOSSIER
```


# Limites connues du prototype
Nous avons identifié plusieurs limites :

* Le réseau électrique est simplifié : le graphe utilisé est un modèle pédagogique. Il ne représente pas fidèlement le réseau de transport d'électricité français ni les contraintes physiques réelles.
* Les données sont statiques : les informations des centrales (production actuelle, disponibilité, capacités) proviennent d'un fichier JSON et ne sont pas mises à jour en temps réel.
* Le modèle de pertes est simplifié : les pertes énergétiques sont estimées à partir des données du fichier et ne prennent pas en compte les phénomènes électriques réels (tension, intensité, congestion du réseau, etc.).
* Le moteur traite une seule augmentation de consommation à la fois. Il ne gère pas plusieurs demandes simultanées ni l'évolution continue de la consommation.
* Le moteur est uniquement prescriptif. Il ne réalise aucune prévision de consommation à partir de données historiques ou météorologiques.
* Le moteur recherche le chemin le plus court pour relier une centrale à toutes les centrales présentes sur la metropole.
* Les coefficients de pondération (distance_weight, loss_weight, saturation_weight, etc.) ont été définis pour le prototype afin de prioriser les centrales. Ils n'ont pas été déterminés à partir de données réelles ni validés sur un réseau électrique


