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

type AssistantData =
  | PlantsResponse
  | ProductionNationaleResponse
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