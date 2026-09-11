
import { CommonModule, DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { History } from '../../services/history';



@Component({
  imports: [CommonModule, DatePipe],
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

