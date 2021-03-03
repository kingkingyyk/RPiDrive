import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { StorageProvider, InitializeSystem, GetStorageProviderTypesResponse, Login, User, Playlist } from 'src/app/drive/models';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CommonService {
  private static URL_DRIVE_ROOT = '/drive/web-api/';
  private static URL_GET_STORAGE_PROVIDER_TYPES = 'storage-provider-types';
  private static URL_GET_STORAGE_PROVIDER_PERMISSIONS = 'storage-provider-permissions';
  private static URL_GET_STORAGE_PROVIDERS: string = 'storage-providers';
  private static URL_CREATE_STORAGE_PROVIDER: string = 'storage-providers/create';
  private static URL_INDEX_STORAGE_PROVDER: string = 'storage-providers/<id>/index';
  private static URL_MANAGE_STORAGE_PROVDER: string = 'storage-providers/<id>';

  private static URL_FILES: string = 'files/<id>';
  private static URL_FILE_DOWNLOAD: string = '/drive/download/<id>'

  private static URL_GET_PLAYLISTS: string = 'playlists';
  private static URL_CREATE_PLAYLIST: string = 'playlists/create';
  private static URL_PLAYLISTS: string = 'playlists/<id>';

  private static URL_INITIALIZE_SYSTEM: string = 'system/initialize';

  private static URL_IS_LOGGED_IN = 'auth/logged-in';
  private static URL_LOGIN = 'auth/login';
  private static URL_LOGOUT = 'auth/logout';

  private static URL_USERS = 'users';
  private static URL_CREATE_USER = 'users/create';
  private static URL_CURRENT_USER = 'users/current';
  private static URL_USER = 'users/<id>';

  private static URL_NETWORK_USAGE = 'system/network-usage';
  private static URL_SYSTEM_INFO = 'system/info';

  constructor(private http: HttpClient) { }

  // ================ SHARED ===============
  private constructDriveAPIUrl(cont: string) {
    return CommonService.URL_DRIVE_ROOT + cont;
  }

  private constructFileUrl(id: string) {
    return this.constructDriveAPIUrl(CommonService.URL_FILES.replace('<id>', id));
  }

  public getFileDownloadUrl(id: string) {
    return CommonService.URL_FILE_DOWNLOAD.replace('<id>', id);
  }

  private constructUserUrl(id: number) {
    return this.constructDriveAPIUrl(CommonService.URL_USER.replace('<id>', id.toString()));
  }

  private constructPlaylistUrl(id: string) {
    return this.constructDriveAPIUrl(CommonService.URL_PLAYLISTS.replace('<id>', id));
  }
  // ================ STORAGE PROVIDER ===============
  getStorageProviderTypes(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_GET_STORAGE_PROVIDER_TYPES), { withCredentials: true });
  }

  getStorageProviderPermissions(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_GET_STORAGE_PROVIDER_PERMISSIONS), { withCredentials: true });
  }

  getStorageProviders(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_GET_STORAGE_PROVIDERS), { withCredentials: true });
  }

  createStorageProvider(storageProvider: StorageProvider): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_CREATE_STORAGE_PROVIDER),
      storageProvider, { withCredentials: true });
  }

  storageProviderPerformIndex(id: number): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_INDEX_STORAGE_PROVDER.replace('<id>', id.toString())),
      {}, { withCredentials: true });
  }

  getStorageProvider(id: number, permissions: boolean): Observable<any> {
    const reqParams = new HttpParams()
      .set('permissions', permissions ? 'true' : 'false');
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_MANAGE_STORAGE_PROVDER.replace('<id>', id.toString())),
      { params: reqParams, withCredentials: true });
  }

  updateStorageProvider(storageProvider: StorageProvider): Observable<any> {
    const reqParams = new HttpParams()
    .set('action', 'basic');
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_MANAGE_STORAGE_PROVDER.replace('<id>', storageProvider.id.toString())),
      storageProvider, { params: reqParams, withCredentials: true });
  }

  updateStorageProviderPermissions(storageProvider: StorageProvider): Observable<any> {
    const reqParams = new HttpParams()
    .set('action', 'permissions');
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_MANAGE_STORAGE_PROVDER.replace('<id>', storageProvider.id.toString())),
      storageProvider, { params: reqParams, withCredentials: true });
  }

  deleteStorageProvider(id: number): Observable<any> {
    return this.http.delete(this.constructDriveAPIUrl(CommonService.URL_MANAGE_STORAGE_PROVDER.replace('<id>', id.toString())), { withCredentials: true });
  }

  // ================ SYSTEM ===============
  isSystemInitialized(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_INITIALIZE_SYSTEM), { withCredentials: true });
  }

  initializeSystem(is: InitializeSystem): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_INITIALIZE_SYSTEM), is, { withCredentials: true });
  }

  isLoggedIn(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_IS_LOGGED_IN), { withCredentials: true });
  }

  login(login: Login): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_LOGIN), login, { withCredentials: true });
  }

  logout(): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_LOGOUT), {}, { withCredentials: true });
  }

  // ================ FILE OBJECT ===============
  getFolder(id: string): Observable<any> {
    const reqParams = new HttpParams()
      .set('action', 'entity')
      .set('traceParents', 'true')
      .set('traceChildren', 'true')
      .set('traceStorageProvider', 'true');
    return this.http.get(this.constructFileUrl(id), { params: reqParams, withCredentials: true });
  }

  getFile(id: string): Observable<any> {
    const reqParams = new HttpParams()
      .set('action', 'entity')
      .set('metadata', 'true');
    return this.http.get(this.constructFileUrl(id), { params: reqParams, withCredentials: true });
  }

  getFileMetadata(id: string): Observable<any> {
    const reqParams = new HttpParams()
      .set('action', 'metadata');
    return this.http.get(this.constructFileUrl(id), { params: reqParams, withCredentials: true });
  }

  downloadFile(id: string) {
    window.open(this.getFileDownloadUrl(id), '_blank');
  }

  renameFile(id: string, name: string): Observable<any> {
    const reqParams = new HttpParams()
      .set('action', 'rename');
    const data = {
      name: name
    };
    return this.http.post(this.constructFileUrl(id), data, { params: reqParams, withCredentials: true });
  }

  moveFile(id: string, destId: string, strategy: string): Observable<any> {
    const reqParams = new HttpParams()
      .set('action', 'move');
    const data = {
      'destination': destId,
      'strategy': strategy
    };
    return this.http.post(this.constructFileUrl(id), data, { params: reqParams, withCredentials: true });
  }

  createFolder(parentId: string, name: string): Observable<any> {
    const reqParams = new HttpParams()
      .set('action', 'new-folder');
    const data = {
      name: name
    };
    return this.http.post(this.constructFileUrl(parentId), data, { params: reqParams, withCredentials: true });
  }

  uploadFiles(parentId: string, formData: FormData): Observable<any> {
    const reqParams = new HttpParams()
      .set('action', 'new-files');
    return this.http.post(this.constructFileUrl(parentId), formData, { params: reqParams, reportProgress: true, withCredentials: true });
  }

  deleteFile(id: string): Observable<any> {
    return this.http.delete(this.constructFileUrl(id), { withCredentials: true });
  }

  getFileContent(id: string): Observable<any> {
    return this.http.get(this.getFileDownloadUrl(id), { responseType: 'text', withCredentials: true });
  }

  getMusicAlbumImageUrl(id: string): string {
    return this.constructFileUrl(id) + '?action=album-image';
  }

  getMusicAlbumImage(id: string): Observable<Blob> {
    const httpHeaders = new HttpHeaders()
      .set('Accept', "image/webp,*/*");
    const reqParams = new HttpParams()
      .set('action', 'album-image');
    return this.http.get(this.constructFileUrl(id), { params: reqParams, headers: httpHeaders, responseType: 'blob', withCredentials: true });
  }

  searchFile(kw: string): Observable<any> {
    const reqParams = new HttpParams()
      .set('keyword', kw);
    return this.http.get(this.constructFileUrl('search'), { params: reqParams, withCredentials: true });
  }

  // ================ PLAYLIST ===============
  getPlaylists(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_GET_PLAYLISTS), { withCredentials: true });
  }

  createPlaylist(playlist: any): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_CREATE_PLAYLIST), playlist, { withCredentials: true });
  }

  getPlaylist(id: string): Observable<any> {
    return this.http.get(this.constructPlaylistUrl(id), { withCredentials: true });
  }

  savePlaylist(id: string, data: any): Observable<any> {
    return this.http.post(this.constructPlaylistUrl(id), data, { withCredentials: true });
  }

  deletePlaylist(id: string): Observable<any> {
    return this.http.delete(this.constructPlaylistUrl(id), { withCredentials: true });
  }

  // ================ USER ===============
  getUsers(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_USERS), { withCredentials: true });
  }

  createUser(user: User): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_CREATE_USER), user, { withCredentials: true });
  }

  getUser(id: number): Observable<any> {
    return this.http.get(this.constructUserUrl(id), { withCredentials: true });
  }

  updateUser(id: number, user: User): Observable<any> {
    return this.http.post(this.constructUserUrl(id), user, { withCredentials: true });
  }

  deleteUser(id: number): Observable<any> {
    return this.http.delete(this.constructUserUrl(id), { withCredentials: true });
  }

  getCurrentUser(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_CURRENT_USER), { withCredentials: true });
  }
  // ================ NETWORK ===============
  getNetworkUsage(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_NETWORK_USAGE), { withCredentials: true });
  }

  // ================ SYSTEM INFO ===============
  getSystemInfo(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_SYSTEM_INFO), { withCredentials: true });
  }
}
