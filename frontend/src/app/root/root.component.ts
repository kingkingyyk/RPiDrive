import { Component, OnInit } from '@angular/core';

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
  selector: 'app-root',
  templateUrl: './root.component.html',
  styleUrls: ['./root.component.css']
})
export class RootComponent implements OnInit {
  apps : App[];

  constructor() {
    this.apps = [new App('File Explorer', 'storage', '/drive/folder'),
                 new App('Media Player', 'play_arrow', 'media-player')]

  }

  ngOnInit(): void {
  }

  openApp(app : App) : void {
    window.open(app.url, '_self')
  }
}
