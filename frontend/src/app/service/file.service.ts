import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from  '@angular/common/http';
import {Observable} from 'rxjs'

@Injectable({
  providedIn: 'root'
})
export class FileService {
  API_URL  =  'http://localhost:8000';
  constructor(private  httpClient:  HttpClient) {}
  getFolderRedirect(folderId : string) {
    return this.httpClient.get(`${this.API_URL}/drive/angular-api/folder-redirect/${folderId}`);
  }
  getFileList(parentFolder: string) {
    let params = new HttpParams()
    if (parentFolder) params = params.append('parent-folder', parentFolder)
    let files = this.httpClient.get(`${this.API_URL}/drive/angular-api/child-files`,
                                {params: params});
    return files;
  }
  getFileNameList(parent_folder: string) {
    let params = new HttpParams()
    if (parent_folder) params = params.append('parent-folder', parent_folder)
    return this.httpClient.get(`${this.API_URL}/drive/angular-api/child-filenames`, {params: params});
  }
  getStorageList() {
    return this.httpClient.get(`${this.API_URL}/drive/angular-api/storages`);
  }
  getFileDownloadURL(fileId: string) {
    return `${this.API_URL}/drive/download/${fileId}`
  }
  downloadFile(fileId: string) {
    window.open(this.getFileDownloadURL(fileId), "_blank");
  }
  getCodeContent(fileId: string) {
    return this.httpClient.get(this.getFileDownloadURL(fileId), {responseType: "text"});
  }
  createNewFolder(folderId: string, newFolderName: string) {
    let data = {'folder-id': folderId, 'name': newFolderName};
    return this.httpClient.post(`${this.API_URL}/drive/angular-api/create-new-folder`, JSON.stringify(data));
  }
  deleteFiles(fileId : string []) {
    return this.httpClient.post(`${this.API_URL}/drive/angular-api/delete-files`, JSON.stringify(fileId));
  }
  getSystemFacts() {
    return this.httpClient.get(`${this.API_URL}/drive/angular-api/system-facts`)
  }
  getNetworkFacts() {
    return this.httpClient.get(`${this.API_URL}/drive/angular-api/network-facts`)
  }
}
