import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpRequest } from  '@angular/common/http';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FileService {
  API_URL  =  environment.api_url;
  constructor(private  httpClient:  HttpClient) {}
  getFolderRedirect(folderId : string) {
    return this.httpClient.get(this.API_URL+'drive/angular-api/folder-redirect/'+folderId);
  }
  getFileList(parentFolder: string) {
    let params = new HttpParams()
    if (parentFolder) params = params.append('parent-folder', parentFolder)
    let files = this.httpClient.get(this.API_URL+'drive/angular-api/child-files',
                                {params: params});
    return files;
  }
  getFolderList(parentFolder: string) {
    let params = new HttpParams()
    if (parentFolder) params = params.append('parent-folder', parentFolder)
    let folders = this.httpClient.get(this.API_URL+'drive/angular-api/child-folders',
                                {params: params});
    return folders;
  }
  getFileNameList(parent_folder: string) {
    let params = new HttpParams();
    if (parent_folder) params = params.append('parent-folder', parent_folder);
    return this.httpClient.get(this.API_URL+'drive/angular-api/child-filenames', {params: params});
  }
  getStorageList() {
    return this.httpClient.get(this.API_URL+'drive/angular-api/storages');
  }
  getFileDownloadURL(fileId: string) {
    return this.API_URL+'drive/download/'+fileId
  }
  downloadFile(fileId: string) {
    window.open(this.getFileDownloadURL(fileId), "_blank");
  }
  getCodeContent(fileId: string) {
    return this.httpClient.get(this.getFileDownloadURL(fileId), {responseType: "text"});
  }
  uploadFile(folderId: string, formData : FormData) {
    const req = new HttpRequest('POST', this.API_URL+'drive/angular-api/upload-files/'+folderId, formData, {reportProgress: true, withCredentials: true});
    return this.httpClient.request(req)
  }
  createNewFolder(folderId: string, newFolderName: string) {
    let data = {'folder-id': folderId, 'name': newFolderName};
    return this.httpClient.post(this.API_URL+'drive/angular-api/create-new-folder', JSON.stringify(data), {withCredentials: true});
  }
  renameFile(fileId: string, newName: string) {
    let data = {'name': newName};
    return this.httpClient.post(this.API_URL+'drive/angular-api/rename-file/'+fileId, JSON.stringify(data), {withCredentials: true});
  }
  moveFiles(fileId : string [], destFolderId : string) {
    return this.httpClient.post(this.API_URL+'drive/angular-api/move-files/'+destFolderId, JSON.stringify(fileId), {withCredentials: true});
  }
  deleteFiles(fileId : string []) {
    return this.httpClient.post(this.API_URL+'drive/angular-api/delete-files', JSON.stringify(fileId), {withCredentials: true});
  }
  getSystemFacts() {
    return this.httpClient.get(this.API_URL+'drive/angular-api/system-facts')
  }
  getNetworkFacts() {
    return this.httpClient.get(this.API_URL+'drive/angular-api/network-facts')
  }

  addURLDownload(data : any) {
    const req = new HttpRequest('POST', this.API_URL+'drive/angular-api/download/add/url', data, {withCredentials: true});
    return this.httpClient.request(req)
  }
  addMagnetDownload(data : any) {
    const req = new HttpRequest('POST', this.API_URL+'drive/angular-api/download/add/magnet', data, {withCredentials: true});
    return this.httpClient.request(req)
  }
  addTorrentDownload(formData : FormData) {
    const req = new HttpRequest('POST', this.API_URL+'drive/angular-api/download/add/torrent', formData, {reportProgress: true, withCredentials: true});
    return this.httpClient.request(req)
  }
  getDownloads() {
    return this.httpClient.get(this.API_URL+'drive/angular-api/download/list')
  }
  pauseDownload(gid : string) {
    return this.httpClient.put(this.API_URL+'drive/angular-api/download/'+gid+'/pause',{}, {withCredentials: true});
  }
  resumeDownload(gid : string) {
    return this.httpClient.put(this.API_URL+'drive/angular-api/download/'+gid+'/resume',{}, {withCredentials: true});
  }
  cancelDownload(gid : string) {
    return this.httpClient.delete(this.API_URL+'drive/angular-api/download/'+gid+'/cancel', {withCredentials: true});
  }
}
