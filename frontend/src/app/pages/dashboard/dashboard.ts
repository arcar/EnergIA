import { Component } from '@angular/core';
import { StatCard } from '../../components/stat-card/stat-card';

@Component({
  selector: 'app-dashboard',
  imports: [StatCard],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard {

}