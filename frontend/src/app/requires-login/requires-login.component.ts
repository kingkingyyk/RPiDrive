import { Component, OnInit } from '@angular/core';
import { UserService } from '../service/user.service';
import { environment } from 'src/environments/environment';

interface CurrentUserResponse {
  loggedIn: boolean;
  superuser: boolean;
}
@Component({
  selector: 'snippet-requires-login',
  templateUrl: './requires-login.component.html',
  styleUrls: ['./requires-login.component.css']
})
export class RequiresLoginComponent implements OnInit {

  constructor(private service : UserService) { }

  ngOnInit(): void {
    if (environment.production) {
      this.service.getCurrentUser().subscribe((data : CurrentUserResponse) => {
        if (!data.loggedIn) window.open('/drive/login', '_self');
      }, error => {
      }).add();
    }
  }

}
