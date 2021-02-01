import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { StorageProvider, InitializeSystem, GetStorageProviderTypesResponse, Login } from 'src/app/drive/models';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CommonService {
  private static URL_DRIVE_ROOT = '/drive/web-api/';
  private static URL_GET_STORAGE_PROVIDER_TYPES = 'storage-provider-types';
  private static URL_GET_STORAGE_PROVIDERS: string = 'storage-providers';
  private static URL_CREATE_STORAGE_PROVIDER: string = 'storage-providers/create';
  private static URL_INDEX_STORAGE_PROVDER: string = 'storage-providers/<id>/index';
  private static URL_MANAGE_STORAGE_PROVDER: string = 'storage-providers/<id>';

  private static URL_FILES: string = 'files/<id>';
  private static URL_INITIALIZE_SYSTEM: string = 'system/initialize';

  private static URL_IS_LOGGED_IN = 'auth/logged-in';
  private static URL_LOGIN = 'auth/login';
  private static URL_LOGOUT = 'auth/logout';

  constructor(private http: HttpClient) { }

  private constructDriveAPIUrl(cont: string) {
    return CommonService.URL_DRIVE_ROOT+cont;
  }

  getStorageProviderTypes(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_GET_STORAGE_PROVIDER_TYPES));
  }

  getStorageProviders(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_GET_STORAGE_PROVIDERS));
  }

  createStorageProvider(storageProvider: StorageProvider) {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_CREATE_STORAGE_PROVIDER),
                          storageProvider);
  }

  storageProviderPerformIndex(id: number) {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_INDEX_STORAGE_PROVDER.replace('<id>', id.toString())),
                          {});
  }

  getStorageProvider(id: number) {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_MANAGE_STORAGE_PROVDER.replace('<id>', id.toString())));
  }

  updateStorageProvider(storageProvider: StorageProvider) {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_MANAGE_STORAGE_PROVDER.replace('<id>', storageProvider.id.toString())),
                          storageProvider);
  }

  deleteStorageProvider(id: number) {
    return this.http.delete(this.constructDriveAPIUrl(CommonService.URL_MANAGE_STORAGE_PROVDER.replace('<id>', id.toString())));
  }

  isSystemInitialized() {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_INITIALIZE_SYSTEM));
  }

  initializeSystem(is : InitializeSystem) {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_INITIALIZE_SYSTEM), is);
  }

  isLoggedIn(): Observable<any> {
    return this.http.get(this.constructDriveAPIUrl(CommonService.URL_IS_LOGGED_IN));
  }

  login(login: Login): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_LOGIN), login);
  }

  logout(): Observable<any> {
    return this.http.post(this.constructDriveAPIUrl(CommonService.URL_LOGOUT), {});
  }

}
