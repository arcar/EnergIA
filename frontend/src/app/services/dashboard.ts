import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DashboardState {
  time: string;
  totalConsumptionMw: number;
  nuclearProductionMw: number;
  solarProductionMw: number;
  windProductionMw: number;
  unmetDemandMw: number;
  availableReserveMw: number;
  status: string;
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {

  private apiUrl = 'http://localhost:3000/dashboard';

  constructor(private http: HttpClient) {}

  getDashboard(): Observable<DashboardState[]> {
    return this.http.get<DashboardState[]>(this.apiUrl);
  }
}