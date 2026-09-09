import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { StatCard } from '../../components/stat-card/stat-card';
import { DashboardService } from '../../services/dashboard';
import { ChangeDetectorRef } from '@angular/core';
import { SimulationService } from '../../services/simulation';
import { SimulationState } from '../../services/simulation-state';

@Component({
  selector: 'app-dashboard',
 imports: [StatCard, FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard implements OnInit {

  selectedState = 0;
  securityMargin = 15;
  selectedRegion = 'normandie';
  startTime = '08:00';
  endTime = '12:00';
  deltaMw = 0;
  simulationActive = false;
  constructor(
    private dashboardService: DashboardService,
    private simulationService: SimulationService,
    private simulationState: SimulationState,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {

    this.simulationState.simulation$.subscribe((data)=>{
    if(!data){
        return;
      }
      this.simulationActive = true;
      const states=data.states;
      this.states=states.map((state:any,index:number)=>({
        index,
        time:state.time,
        consommation:state.totalConsumptionMw,
        nucleaire:state.nuclearProductionMw,
        reserve:state.availableReserveMw,
        centralesDisponibles:'18 / 18',
        solaire:state.solarProductionMw,
        eolienne:state.windProductionMw,
        demandeResiduelle:state.totalConsumptionMw-state.solarProductionMw-state.windProductionMw,
        status:state.status,
        unmetDemand:state.unmetDemandMw
      }));
      const debut=this.timeline.findIndex(state=>state.time===data.parameters.start);
      const fin=this.timeline.findIndex(state=>state.time===data.parameters.end);
      if(debut!==-1&&fin!==-1){
        this.perturbationStates=this.states.slice(debut,fin+1);
         this.selectedState=debut;
      }
      this.cdr.detectChanges();
    });

    this.dashboardService.getDashboard().subscribe({
      next: (data) => {
       
        if(this.simulationActive){
          return;
        }
        this.states = data.map((state, index) => ({
          index,
          time: state.time,
          consommation: state.totalConsumptionMw,
          nucleaire: state.nuclearProductionMw,
          reserve: state.availableReserveMw,
          centralesDisponibles: '18 / 18',
          solaire: state.solarProductionMw,
          eolienne: state.windProductionMw,
          demandeResiduelle: state.totalConsumptionMw - state.solarProductionMw - state.windProductionMw,
          status: state.status,
          unmetDemand: state.unmetDemandMw
        }));
        
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Erreur dashboard :', error);
      }
    });
  }

  timeline = Array.from({ length: 96 }, (_, index) => {

    const hours = Math.floor(index / 4);

    const minutes = (index % 4) * 15;

    return {
      index,
      time: `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
    };

  });

  states: any[] = [];
  perturbationStates: any[] = [];


  selectState(index: number): void {

    this.selectedState = index;

  }


  get currentState() {
    return this.states[this.selectedState] ?? {
      consommation: 0,
      nucleaire: 0,
      reserve: 0,
      centralesDisponibles: '0 / 0',
      solaire: 0,
      eolienne: 0,
      demandeResiduelle: 0,
      time: '00:00'
    };
  }


  get networkStatus(): string {
    if (this.currentState.status === 'insufficient') {
      return 'Demande non satisfaite';
    }
    if (this.currentState.status === 'degraded') {
      return 'Situation dégradée';
    }
    return 'Situation normale';
  }


  get networkStatusClass(): string {
    if (this.currentState.status === 'insufficient') {
      return 'danger';
    }
    if (this.currentState.status === 'degraded') {
      return 'warning';
    }
    return 'normal';
  }

 
  appliquerPerturbation(): void {
      const heureSelectionnee=this.timeline[this.selectedState].time;
      const selectionDansPlage=heureSelectionnee>=this.startTime&&heureSelectionnee<=this.endTime;
      this.simulationService.perturberConsommation(
        this.selectedRegion,
        this.startTime,
        this.endTime,
        this.deltaMw
      ).subscribe({
        next:(data)=>{
          this.states=data.map((state:any,index:number)=>({
            index,
            time:state.time,
            consommation:state.totalConsumptionMw,
            nucleaire:state.nuclearProductionMw,
            reserve:state.availableReserveMw,
            centralesDisponibles:'18 / 18',
            solaire:state.solarProductionMw,
            eolienne:state.windProductionMw,
            demandeResiduelle:state.totalConsumptionMw-state.solarProductionMw-state.windProductionMw,
            status:state.status,
            unmetDemand:state.unmetDemandMw
          }));
          const debut=this.timeline.findIndex(state=>state.time===this.startTime);
          const fin=this.timeline.findIndex(state=>state.time===this.endTime);
          this.perturbationStates=this.states.slice(debut,fin+1);
          if(!selectionDansPlage){
            const nouvelIndex=this.timeline.findIndex(state=>state.time===this.startTime);
            if(nouvelIndex!==-1){
              this.selectedState=nouvelIndex;
            }
          }
          this.cdr.detectChanges();
        },
        error:(error)=>{
          console.error('Erreur perturbation :',error);
        }
      });
  }

}

