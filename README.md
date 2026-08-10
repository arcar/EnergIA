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
```


# Lancement de l’application
Ouvrir docker desktop.

Depuis la racine du projet :

```bash
docker compose up -d
```

Cela va permettre de démarrer les conteneurs présents dans le docker compose.


# Exécution des tests


# Routes disponibles
Toutes les routes sont disponibles depuis la Gateway : http://localhost:3000

## Centrales

### Obtenir toutes les centrales

```
GET /plants
```

---

### Obtenir toutes les routes pour une région

```
GET /plants/routes
```

Params :
```
"regionId" : "occitanie"
```


---

### Obtenir toutes les regions

```
GET /plants/region
```

---


### Simuler une augmentation de la consommation pour une région donnée

```
POST /simulation
```

Body :

```json
{
    "region":"Normandie",
    "augmentation":"500"
}
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


# Limites connues du prototype
Nous avons identifié plusieurs limites :

* Le réseau électrique est simplifié : le graphe utilisé est un modèle pédagogique. Il ne représente pas fidèlement le réseau de transport d'électricité français ni les contraintes physiques réelles.
* Les données sont statiques : les informations des centrales (production actuelle, disponibilité, capacités) proviennent d'un fichier JSON et ne sont pas mises à jour en temps réel.
* Le modèle de pertes est simplifié : les pertes énergétiques sont estimées à partir des données du fichier et ne prennent pas en compte les phénomènes électriques réels (tension, intensité, congestion du réseau, etc.).
* Le moteur traite une seule augmentation de consommation à la fois. Il ne gère pas plusieurs demandes simultanées ni l'évolution continue de la consommation.
* Le moteur est uniquement prescriptif. Il ne réalise aucune prévision de consommation à partir de données historiques ou météorologiques.
* Le moteur recherche le chemin le plus court pour relier une centrale à toutes les centrales présentes sur la metropole.
* Les coefficients de pondération (distance_weight, loss_weight, saturation_weight, etc.) ont été définis pour le prototype afin de prioriser les centrales. Ils n'ont pas été déterminés à partir de données réelles ni validés sur un réseau électrique

## Gestion des validations, logs et erreurs de simulation
Une amélioration de l'API de simulation a été réalisée afin de rendre les échanges plus fiables et plus compréhensibles.

### Validations ajoutées
- Vérification que la région demandée existe avant de lancer une simulation.
- Vérification que l'augmentation de consommation est valide (valeur strictement supérieure à 0 MW).
- Gestion des demandes impossibles lorsque la puissance disponible des centrales locales est insuffisante.

### Gestion des erreurs
- Mise en place de réponses d'erreurs structurées avec un statut, un message explicite et le détail de l'erreur.
- Retour de messages compréhensibles pour faciliter le diagnostic côté utilisateur ou frontend.
- Gestion des erreurs de communication entre la gateway Express et le service FastAPI.

### Ajout des logs
Des journaux ont été ajoutés dans le service de simulation afin de suivre les différentes étapes du traitement :
- Début d'une simulation avec la région et l'augmentation demandée.
- Chargement des données des centrales.
- Calcul des métriques des centrales.
- Nombre de centrales disponibles dans la région demandée.
- Calcul de la demande résiduelle.
- Fin de la répartition de puissance.

# demander les logs en cas de non affichage après compose up
```
docker compose logs -f NOM_DOSSIER
```