import os 
import json

parent = os.path.dirname(os.path.abspath(__file__))
parc_non_pilotable_data = os.path.join(parent, "data", "energia-production-non-pilotable.json")

with open(parc_non_pilotable_data, "r", encoding="utf-8") as fichier:
    data = json.load(fichier)

#-----------------------------------------
# SOLAIRE
#------------------------------------------













#-----------------------------------------
# EOLIEN
#------------------------------------------











#-----------------------------------------
# demande résiduelle
#------------------------------------------