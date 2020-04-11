import { Component, OnInit, OnDestroy } from '@angular/core';
import { FileService } from 'src/app/service/file.service';
import { timer } from 'rxjs';

@Component({
  selector: 'app-system-facts',
  templateUrl: './system-facts.component.html',
  styleUrls: ['./system-facts.component.css']
})
export class SystemFactsComponent implements OnInit, OnDestroy {
  cpu : object;
  memory : object;
  sensors : object;
  environment : object;
  loaded : boolean;
  timer : any;

  constructor(private fileService: FileService) {}

  ngOnInit() {
    this.timer = timer(0, 5000).subscribe(() => {
      this.loadData();
    })
  }

  ngOnDestroy() {
    if (this.timer) this.timer.unsubscribe();
  }

  loadData() {
    this.fileService.getSystemFacts().subscribe((data:  object) => this.setData(data));
  }

  setData(data: object) {
    this.loaded = true;
    this.cpu = data['system_data']['CPU'];
    this.memory = data['system_data']['Memory'];
    this.sensors = data['system_data']['Sensors'];
    this.environment = data['system_data']['Environment'];
  }
}
