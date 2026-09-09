import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn:'root'
})
export class SimulationService{

  private apiUrl='http://localhost:8000';

  constructor(private http:HttpClient){}

  perturberConsommation(region:string,start:string,end:string,deltaMw:number):Observable<any>{
    return this.http.post(`${this.apiUrl}/perturber_consommation`,{
      id_region:region,
      start,
      end,
      deltaMw
    });
  }

}