import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface SimulationData {
  states:any[];
  parameters:{
    id_region:string;
    start:string;
    end:string;
    deltaMw:number;
  };
}

@Injectable({
  providedIn:'root'
})
export class SimulationState {
  private simulationSubject=new BehaviorSubject<SimulationData|null>(null);
  simulation$=this.simulationSubject.asObservable();

  setSimulation(data:SimulationData):void {
    this.simulationSubject.next(data);
  }
}