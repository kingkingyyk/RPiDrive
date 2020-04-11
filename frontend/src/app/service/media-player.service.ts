import { Injectable } from '@angular/core';
import { HttpClient } from  '@angular/common/http';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class MediaPlayerService {
  API_URL  =  environment.api_url + 'media-player/angular-api';
  constructor(private  httpClient:  HttpClient) {}
  searchPlaylists(kw : string) {
    return this.httpClient.get(`${this.API_URL}/playlists/search`, {params: {name: kw}});
  }
  getPlaylists() {
    return this.httpClient.get(`${this.API_URL}/playlists`);
  }
  createPlaylist(name : string) {
    return this.httpClient.post(`${this.API_URL}/playlist/create`, JSON.stringify({'name': name}));
  }
  getPlaylist(playlistId : string) {
    return this.httpClient.get(`${this.API_URL}/playlist/`+playlistId);
  }
  updatePlaylist(data : object) {
    return this.httpClient.post(`${this.API_URL}/playlist/`+data['id'], JSON.stringify(data));
  }
  deletePlaylist(data : object) {
    return this.httpClient.delete(`${this.API_URL}/playlist/`+data['id']);
  }
  searchMedia(kw: string) {
    return this.httpClient.get(`${this.API_URL}/media/search`, {params: {name: kw}});
  }
}
