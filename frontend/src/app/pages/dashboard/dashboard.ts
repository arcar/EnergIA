import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { StatCard } from '../../components/stat-card/stat-card';
import { DashboardService } from '../../services/dashboard';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-dashboard',
 imports: [StatCard, FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard implements OnInit {

  selectedState = 0;
  securityMargin = 15;
  constructor(
    private dashboardService: DashboardService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.dashboardService.getDashboard().subscribe({
      next: (data) => {
       
        this.states = data.map((state, index) => ({
          index,
          time: state.time,
          consommation: state.totalConsumptionMw,
          nucleaire: state.nuclearProductionMw,
          reserve: state.availableReserveMw,
          centralesDisponibles: '18 / 18',
          solaire: state.solarProductionMw,
          eolienne: state.windProductionMw,
          demandeResiduelle: state.totalConsumptionMw - state.nuclearProductionMw - state.solarProductionMw - state.windProductionMw
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

    if (this.currentState.demandeResiduelle < 0) {
      return 'Demande non satisfaite';
    }

    if (this.currentState.reserve < 1000) {
      return 'Situation dégradée';
    }

    return 'Situation normale';

  }


  get networkStatusClass(): string {

    if (this.currentState.demandeResiduelle < 0) {
      return 'danger';
    }

    if (this.currentState.reserve < 1000) {
      return 'warning';
    }

    return 'normal';

  }

}

