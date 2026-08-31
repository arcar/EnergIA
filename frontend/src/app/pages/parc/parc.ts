
import { Component } from '@angular/core';

@Component({
  imports: [],
  selector: 'app-parc',
  styleUrl: './parc.scss',
  templateUrl: './parc.html',
})
export class Parc {

  centrales = [
    {
      nom: 'Paluel',
      region: 'Normandie',
      puissance: 5320,
      production: 3032,
      disponible: true
    },
    {
      nom: 'Flamanville',
      region: 'Normandie',
      puissance: 4290,
      production: 2445,
      disponible: true
    },
    {
      nom: 'Penly',
      region: 'Normandie',
      puissance: 2660,
      production: 1516,
      disponible: true
    },
    {
      nom: 'Gravelines',
      region: 'Hauts-de-France',
      puissance: 5460,
      production: 3112,
      disponible: true
    },
    {
      nom: 'Cattenom',
      region: 'Grand Est',
      puissance: 5200,
      production: 2964,
      disponible: true
    },
    {
      nom: 'Chooz',
      region: 'Grand Est',
      puissance: 3000,
      production: 1710,
      disponible: true
    },
    {
      nom: 'Nogent-sur-Seine',
      region: 'Grand Est',
      puissance: 2620,
      production: 1493,
      disponible: true
    },
    {
      nom: 'Bugey',
      region: 'Auvergne-Rhône-Alpes',
      puissance: 3580,
      production: 2041,
      disponible: true
    },
    {
      nom: 'Cruas-Meysse',
      region: 'Auvergne-Rhône-Alpes',
      puissance: 3660,
      production: 2086,
      disponible: true
    },
    {
      nom: 'Saint-Alban',
      region: 'Auvergne-Rhône-Alpes',
      puissance: 2670,
      production: 1522,
      disponible: true
    },
    {
      nom: 'Tricastin',
      region: 'Auvergne-Rhône-Alpes',
      puissance: 3660,
      production: 2086,
      disponible: true
    },
    {
      nom: 'Le Blayais',
      region: 'Nouvelle-Aquitaine',
      puissance: 3640,
      production: 2075,
      disponible: true
    },
    {
      nom: 'Civaux',
      region: 'Nouvelle-Aquitaine',
      puissance: 2990,
      production: 1704,
      disponible: true
    },
    {
      nom: 'Golfech',
      region: 'Occitanie',
      puissance: 2620,
      production: 1493,
      disponible: true
    },
    {
      nom: 'Belleville-sur-Loire',
      region: 'Centre-Val de Loire',
      puissance: 2620,
      production: 1493,
      disponible: true
    },
    {
      nom: 'Chinon',
      region: 'Centre-Val de Loire',
      puissance: 3620,
      production: 2063,
      disponible: true
    },
    {
      nom: 'Dampierre-en-Burly',
      region: 'Centre-Val de Loire',
      puissance: 3560,
      production: 2029,
      disponible: true
    },
    {
      nom: 'Saint-Laurent-des-Eaux',
      region: 'Centre-Val de Loire',
      puissance: 1830,
      production: 1043,
      disponible: true
    }

  ];

}

