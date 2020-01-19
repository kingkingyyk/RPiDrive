import { Component, OnInit } from '@angular/core';
import { NetworkUsageComponent } from './network-usage/network-usage.component'
import { SystemFactsComponent } from './system-facts/system-facts.component'

@Component({
  selector: 'app-system',
  templateUrl: './system.component.html',
  styleUrls: ['./system.component.css']
})
export class SystemComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

}
