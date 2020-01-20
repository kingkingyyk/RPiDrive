import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class FileSelectionService {
  private messageSource = new BehaviorSubject([]);
  currentMessage = this.messageSource.asObservable();

  constructor() { }

  pushUpdate(message: object []) {
    this.messageSource.next(message);
  }
}
