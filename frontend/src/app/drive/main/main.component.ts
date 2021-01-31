import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit {

  constructor(private service: CommonService,
              private router: Router,
              private titleService: Title) {
                this.titleService.setTitle('RPi Drive');
              }

  ngOnInit(): void {
  }

}
