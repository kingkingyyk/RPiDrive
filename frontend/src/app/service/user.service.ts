import { Injectable } from '@angular/core';
import { HttpClient } from  '@angular/common/http';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  API_URL  =  environment.api_url;
  constructor(private  httpClient:  HttpClient) {}
  login(username: string, password: string) {
    let data = {'u': username, 'p': password};
    return this.httpClient.post(this.API_URL+'drive/angular-api/user/login', JSON.stringify(data));
  }
  logout() {
    return this.httpClient.post(this.API_URL+'drive/angular-api/user/logout', '');
  }
  getCurrentUser() {
    return this.httpClient.get(this.API_URL+'drive/angular-api/user/current')
  }
  getUsers() {
    return this.httpClient.get(this.API_URL+'drive/angular-api/users')
  }
  createUser(username: string, password: string, superuser: boolean) {
    let data = {'u': username, 'p': password, 'superuser': superuser};
    return this.httpClient.post(this.API_URL+'drive/angular-api/user/create', JSON.stringify(data));
  }
  updateUser(userId: number, username: string, password: string, superuser: boolean) {
    let data = {'u': username, 'p': password, 'superuser': superuser};
    return this.httpClient.post(this.API_URL+'drive/angular-api/user/'+userId.toString()+'/manage', JSON.stringify(data));
  }
  deleteUser(userId: number) {
    return this.httpClient.delete(this.API_URL+'drive/angular-api/user/'+userId.toString()+'/manage');
  }
}
