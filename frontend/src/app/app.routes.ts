import { Routes } from '@angular/router';
import { Dashboard } from './pages/dashboard/dashboard';
import { Simulation } from './pages/simulation/simulation';
import { Parc } from './pages/parc/parc';
import { Historique } from './pages/historique/historique';

export const routes: Routes = [
  {
    path: '',
    component: Dashboard
  },
  {
    path: 'simulation',
    component: Simulation
  },
  {
    path: 'parc',
    component: Parc
  },
  {
    path: 'historique',
    component: Historique
  }
];