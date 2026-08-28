import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { StatCard } from '../../components/stat-card/stat-card';

@Component({
  selector: 'app-dashboard',
 imports: [StatCard, FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard {

  selectedState = 0;
  securityMargin = 15;


  timeline = Array.from({ length: 96 }, (_, index) => {

    const hours = Math.floor(index / 4);

    const minutes = (index % 4) * 15;

    return {
      index,
      time: `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
    };

  });


  states = this.timeline.map((state) => {

    return {
      index: state.index,
      time: state.time,

      consommation: 52000 + state.index * 20,

      nucleaire: 50000 + state.index * 15,

      reserve: 8400 - state.index * 5,

      centralesDisponibles: '18 / 18',

      solaire: Math.max(
        0,
        Math.round(
          4200 * Math.sin((Math.PI * state.index) / 96)
        )
      ),

      eolienne: 2250 + (state.index % 8) * 80,

      demandeResiduelle: 45550 + state.index * 10

    };

  });


  selectState(index: number): void {

    this.selectedState = index;

  }


  get currentState() {

    return this.states[this.selectedState];

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

