import { Component, input } from '@angular/core';

@Component({
  selector: 'app-stat-card',
  imports: [],
  templateUrl: './stat-card.html',
  styleUrl: './stat-card.scss'
})
export class StatCard {

  title = input<string>('');

  value = input<string>('');

  unit = input<string>('');

  icon = input<string>('');

}