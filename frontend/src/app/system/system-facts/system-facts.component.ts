import { Component, OnInit } from '@angular/core';
import { FileService } from 'src/app/service/file.service';
import { interval } from 'rxjs';
import { flatMap } from 'rxjs/operators'

@Component({
  selector: 'app-system-facts',
  templateUrl: './system-facts.component.html',
  styleUrls: ['./system-facts.component.css']
})
export class SystemFactsComponent implements OnInit {
  cpu : object;
  memory : object;
  sensors : object;
  environment : object;
  loaded : boolean;

  constructor(private fileService: FileService) {}

  ngOnInit() {
    this.fileService.getSystemFacts().subscribe((data:  object) => this.setData(data));

    interval(5*1000)
    .pipe(
        flatMap(() => this.fileService.getSystemFacts())
    )
    .subscribe((data:  object) => this.setData(data));
  }

  setData(data: object) {
    this.loaded = true;
    this.cpu = data['system_data']['CPU'];
    this.memory = data['system_data']['Memory'];
    this.sensors = data['system_data']['Sensors'];
    this.environment = data['system_data']['Environment'];
  }
}
