import { Component, OnInit } from '@angular/core';
import { UserService } from '../service/user.service';
import { environment } from 'src/environments/environment';
import { Title } from '@angular/platform-browser';

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
interface CurrentUserResponse {
  loggedIn: boolean;
  superuser: boolean;
}
@Component({
  selector: 'app-root',
  templateUrl: './root.component.html',
  styleUrls: ['./root.component.css']
})
export class RootComponent implements OnInit {
  loadingCurrentUser = false;
  loadingCurrentUserError = false;
  apps : App[];

  constructor(private userService : UserService,
              private titleService : Title) {}

  ngOnInit(): void {
    this.titleService.setTitle('RPiDrive Menu');
    if (environment.production) {
      this.loadingCurrentUser = true;
      this.loadingCurrentUserError = false;
      this.userService.getCurrentUser().subscribe((data : CurrentUserResponse) => {
        if (data.loggedIn) {
          this.createApps(data.superuser);
        } else window.open('/drive/login', '_self');
      }, error => {
        this.loadingCurrentUserError = false;
      }).add(() => this.loadingCurrentUser = false);
    } else this.createApps(true);
  }

  createApps(isSuperuser : boolean) {
    if (isSuperuser) {
      this.apps = [new App('File Explorer', 'storage', '/drive/folder'),
                  new App('Media Player', 'play_arrow', '/drive/media-player'),
                  new App('System', 'settings', '/drive/system')]
    } else {
      this.apps = [new App('File Explorer', 'storage', '/drive/folder'),
                  new App('Media Player', 'play_arrow', '/drive/media-player'),
      ]
    }
  }
  openApp(app : App) : void {
    window.open(app.url, '_self')
  }

  logout() {
    this.userService.logout().subscribe((data : object) => {}).add(() => window.open('/drive/login', '_self'));
  }
}
