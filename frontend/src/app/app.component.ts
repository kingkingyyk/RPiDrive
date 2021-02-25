import { Component, OnDestroy, OnInit } from '@angular/core';
import { IsLoggedInResponse } from './drive/models';
import { Url } from './drive/urls';
import { CommonService } from './services/common.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'frontend';
}

@Component({
  selector: 'periodic-check-login',
  template: '',
})
export class CheckLoginComponent implements OnInit, OnDestroy {
  timer: any;

  constructor(private service: CommonService) {}

  ngOnInit() { 
    this.timer = setInterval(() => this.check(), 30*1000);
    this.check();
  }
  ngOnDestroy() {if (this.timer) clearInterval(this.timer);}

  check() {
    this.service.isLoggedIn().subscribe((data : IsLoggedInResponse) => {
      if (!data.result) window.open(Url.getLoginAbsURL(), '_self');
    }, error => {
      window.open(Url.getLoginAbsURL(), '_self');
    });
  }

}