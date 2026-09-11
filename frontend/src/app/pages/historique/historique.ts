import { Component } from '@angular/core';
import { History } from '../../services/history';
import { CommonModule } from '@angular/common';


@Component({
  imports: [CommonModule],
  selector: 'app-historique',
  styleUrl: './historique.scss',
  templateUrl: './historique.html',
})
export class Historique {
  simulations: any[] = [];
  constructor(private history: History) {
    this.history.history$.subscribe((simulations) => {
      this.simulations = simulations;
    });
  }
}

