import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';
import { IsLoggedInResponse } from '../models';
import { Url } from '../urls';

class App {
  name: string;
  icon: string;
  url: string;

  constructor(name: string, icon: string, url: string) {
    this.name = name;
    this.icon = icon;
    this.url = url;
  }
}


@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit {
  loadingLevel: number = 0;
  apps : App[];

  constructor(private service: CommonService,
              private router: Router,
              private titleService: Title) {
                this.titleService.setTitle('RPi Drive');
              }

  ngOnInit(): void {
    this.loadingLevel++;

    this.service.isSystemInitialized().subscribe(() => {
      this.checkLogin();
    }, error => {}).add(() => {
      this.loadingLevel--;
    });

    this.createApps();
  }

  checkLogin() {
    this.loadingLevel++;
    this.service.isLoggedIn().subscribe((response : IsLoggedInResponse) => {}, error => {
      this.router.navigateByUrl(Url.getLoginAbsURL());
    }).add(() => {
      this.loadingLevel--;
    });
  }

  createApps() {
    this.apps = [new App('File Explorer', 'storage', Url.getFolderAbsURL()),
    new App('Media Player', 'play_arrow', Url.getMediaPlayerAbsUrl()),
    new App('Settings', 'settings', Url.getSettingsAbsUrl())]
  }

  openApp(app : App) : void {
    window.open(app.url, '_self')
  }

  logout() {
    this.service.logout().subscribe((data : object) => {
    }).add(() => window.open(Url.getLoginAbsURL(), '_self'));
  }

}
