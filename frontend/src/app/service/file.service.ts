import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from  '@angular/common/http';
import {Observable} from 'rxjs'

@Injectable({
  providedIn: 'root'
})
export class FileService {
  API_URL  =  'http://localhost:8000';
  constructor(private  httpClient:  HttpClient) {}
  getFileList(parent_folder: string) {
    let params = new HttpParams()
    if (parent_folder) {
      params = params.append('parent-folder', parent_folder)
    }
    let files = this.httpClient.get(`${this.API_URL}/drive/angular-api/child-files`,
                                {params: params});
    return files;
  }
  getStorageList() {
    return this.httpClient.get(`${this.API_URL}/drive/angular-api/storages`);
  }
  getFileDownloadURL(fileId: string) {
    return `${this.API_URL}/drive/angular-api/download/${fileId}`
  }
  downloadFile(fileId: string) {
    window.open(this.getFileDownloadURL(fileId), "_blank");
  }
  getCodeContent(fileId: string) {
    return this.httpClient.get(this.getFileDownloadURL(fileId), {responseType: "text"});
  }
  createNewFolder(folderId: string, newFolderName: string) {
    return null;
    //return this.httpClient.post(`${this.API_URL}/drive/angular-api/create-new-folder/${folderId}`, );
  }
}
