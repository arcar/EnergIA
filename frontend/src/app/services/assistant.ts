import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface PlantsResponse {
  count: number;
  plants: string[];
}

interface ProductionNationaleResponse {
  success: boolean;
  heure: string;
  production_nationale_mw: number;
  resultats: unknown[];
}

interface ConsoRegionResponse {
  region: string;
  heure: string;
  consommation: number;
}

interface PerturbationResponse {
  parameters: {
    id_region: string;
    start: string;
    end: string;
    deltaMw: number;
  };
  states: unknown[];
}

type AssistantData =
  | PlantsResponse
  | ProductionNationaleResponse
  | ConsoRegionResponse
  | PerturbationResponse
  | string;

interface AssistantResponse {
  response: AssistantData;
}

@Injectable({
  providedIn: 'root'
})
export class AssistantService {
  private apiUrl = 'http://localhost:3002/api/chat';

  constructor(private http: HttpClient) {}

  sendMessage(prompt: string): Observable<AssistantResponse> {
    return this.http.post<AssistantResponse>(this.apiUrl, {
      prompt
    });
  }
}