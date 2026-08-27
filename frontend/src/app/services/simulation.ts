import { Injectable } from '@angular/core';
import { Simulation as SimulationState } from '../models/simulation';

@Injectable({
  providedIn: 'root'
})
export class SimulationService {

  private simulationStates: SimulationState[] = [];

}