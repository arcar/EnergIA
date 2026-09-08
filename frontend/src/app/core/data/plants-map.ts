export interface PlantMap {
  id: string;
  region: string;
  x: number;
  y: number;
}

export const PLANTS_MAP: PlantMap[] = [
  { id: 'Gravelines', region: 'Hauts-de-France', x: 142, y: 92 },
  { id: 'Chooz', region: 'Grand Est', x: 425, y: 108 },
  { id: 'Cattenom', region: 'Grand Est', x: 455, y: 145 },
  { id: 'Flamanville', region: 'Normandie', x: 115, y: 142 },
  { id: 'Paluel', region: 'Normandie', x: 155, y: 155 },
  { id: 'Penly', region: 'Normandie', x: 190, y: 160 },
  { id: 'Nogent-sur-Seine', region: 'Grand Est', x: 355, y: 195 },
  { id: 'Dampierre-en-Burly', region: 'Centre-Val de Loire', x: 315, y: 255 },
  { id: 'Saint-Laurent-des-Eaux', region: 'Centre-Val de Loire', x: 285, y: 265 },
  { id: 'Belleville-sur-Loire', region: 'Centre-Val de Loire', x: 350, y: 275 },
  { id: 'Chinon', region: 'Centre-Val de Loire', x: 235, y: 285 },
  { id: 'Civaux', region: 'Nouvelle-Aquitaine', x: 245, y: 370 },
  { id: 'Le Blayais', region: 'Nouvelle-Aquitaine', x: 180, y: 425 },
  { id: 'Bugey', region: 'Auvergne-Rhône-Alpes', x: 410, y: 375 },
  { id: 'Saint-Alban', region: 'Auvergne-Rhône-Alpes', x: 395, y: 415 },
  { id: 'Cruas-Meysse', region: 'Auvergne-Rhône-Alpes', x: 405, y: 450 },
  { id: 'Tricastin', region: 'Auvergne-Rhône-Alpes', x: 405, y: 490 },
  { id: 'Golfech', region: 'Occitanie', x: 265, y: 505 }
];