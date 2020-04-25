import { Component, OnInit } from '@angular/core';
import { UserService } from '../service/user.service';
import { Title } from '@angular/platform-browser';

interface CurrentUserResponse {
  loggedIn: boolean;
  superuser: boolean;
}
interface LoginResponse {
  success: boolean;
}
@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  username : string = "";
  password : string = "";
  loggingIn = false;
  failedLogin = false;

  constructor(private service : UserService,
              private titleService: Title) { }

  ngOnInit(): void {
    this.titleService.setTitle('RPiDrive Login')
    this.service.getCurrentUser().subscribe((data : CurrentUserResponse) => {
      if (data.loggedIn) window.open('/drive', '_self');
    });
  }

  login() : void {
    this.loggingIn = true;
    this.failedLogin = false;
    this.service.login(this.username, this.password).subscribe((data : LoginResponse) => {
      this.failedLogin = !data.success;
      if (data.success) window.open('/drive', '_self');
    }, error => {
      this.failedLogin = true;
    }).add(() => this.loggingIn = false);
  }
}
