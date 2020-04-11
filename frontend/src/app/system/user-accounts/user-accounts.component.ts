import { Component, OnInit } from '@angular/core';
import { UserService } from 'src/app/service/user.service';
import { MatDialog, MatSnackBar } from '@angular/material';
import { DeleteComponent } from './delete/delete.component';
import { EditComponent } from './edit/edit.component';

interface UsersResponse {
  values: User [];
}
interface User {
  id: number;
  username: string;
  password: string;
  superuser: boolean;
}
@Component({
  selector: 'app-user-accounts',
  templateUrl: './user-accounts.component.html',
  styleUrls: ['./user-accounts.component.css']
})
export class UserAccountsComponent implements OnInit {
  private static PLACEHOLDER_PASSWORD = 'placeholder here lol';
  displayedColumns = ['id', 'username', 'superuser', 'actions']

  users: User[] = [];

  constructor(private service : UserService,
              private dialog : MatDialog,
              private snackBar: MatSnackBar) { }

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers() : void {
    this.snackBar.open('Loading users...', null, {
      duration: 1000
    });
    this.service.getUsers().subscribe((data : UsersResponse) => {
      this.users = data.values;
    });
  }

  createUser(): void {
    const diag = this.dialog.open(EditComponent, {data: {id: null, username: '', password: ''}});
    diag.afterClosed().subscribe((result : User) => {
      if (result) {
        this.snackBar.open('Create user...', null, {
          duration: 1000
        });
        this.service.createUser(result.username, result.password, result.superuser).subscribe( data => {
          this.loadUsers();
        }, error => {
          this.snackBar.open('Done creating user!', null, {
            duration: 1000
          });
        });
      }
    });
  }

  editUser(user : User) : void {
    user.password = UserAccountsComponent.PLACEHOLDER_PASSWORD;
    const diag = this.dialog.open(EditComponent, {data: user});
    diag.afterClosed().subscribe((result : User) => {
      if (result) {
        if (result.password === UserAccountsComponent.PLACEHOLDER_PASSWORD) result.password = null;
        this.snackBar.open('Updating user...', null, {
          duration: 1000
        });
        this.service.updateUser(result.id, result.username, result.password, result.superuser).subscribe( data => {
          this.loadUsers();
        }, error => {
          this.snackBar.open('Done updating user!', null, {
            duration: 1000
          });
        });
      }
    });
  }

  deleteUser(user : User) : void {
    const diag = this.dialog.open(DeleteComponent, {data: user});
    diag.afterClosed().subscribe(result => {
      if (result) {
        this.snackBar.open('Deleting user...', null, {
          duration: 1000
        });
        this.service.deleteUser(user.id).subscribe( data => {
          this.loadUsers();
        }, error => {
          this.snackBar.open('Done deleting user!', null, {
            duration: 1000
          });
        });
      }
    });
  }
}
