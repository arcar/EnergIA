import { Component } from '@angular/core';
import { PLANTS_MAP, PlantMap } from '../../core/data/plants-map';

@Component({
  selector: 'app-france-map',
  standalone: true,
  imports: [],
  templateUrl: './france-map.html',
  styleUrl: './france-map.scss'
})
export class FranceMap {
  plants: PlantMap[] = PLANTS_MAP;
}