import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface AssistantResponse {
  response: {
    count: number;
    plants: string[];
  } | string;
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