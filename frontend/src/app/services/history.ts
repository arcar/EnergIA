import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
providedIn:'root'
})
export class History{

    private historySubject=new BehaviorSubject<any[]>([]);

    history$=this.historySubject.asObservable();

    addSimulation(simulation:any):void{
        const current=this.historySubject.value;
        this.historySubject.next([
        simulation,
        ...current
        ]);
    }

}