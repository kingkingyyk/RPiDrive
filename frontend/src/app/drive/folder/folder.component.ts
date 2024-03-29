import { AfterViewInit, Component, Inject, Input, OnInit,
         Output, SimpleChanges, ViewChild, EventEmitter,
         ChangeDetectorRef, OnDestroy
       } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { Title } from '@angular/platform-browser';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';
import { FileObject, GetStorageProvidersResponse, StorageProvider, 
         FileObjectType, FileExt, GetStorageProviderTypesResponse, 
         StorageProviderType, FileUploadModel, 
         FilePreviewType, Metadata, SearchResultResponse, User,
         GetUsersResponse, GetStorageProviderPermissionsResponse,
         StorageProviderPermission, StorageProviderUser,
         Job, GetJobsResponse, GenerateQuickAccessKeyResponse,
       } from '../models';
import { MatMenuTrigger } from '@angular/material/menu';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { UntypedFormBuilder, UntypedFormControl, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { SelectionModel } from '@angular/cdk/collections';
import { Url } from '../urls';
import { catchError, debounceTime, distinctUntilChanged, last, map, tap } from 'rxjs/operators';
import { HttpEventType, HttpErrorResponse } from '@angular/common/http';
import { interval, of } from 'rxjs';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { MediaMatcher } from '@angular/cdk/layout';
import { MatSidenav } from '@angular/material/sidenav';

abstract class Utils {
  static isFile(file: FileObject): boolean {
    return file.objType === FileObjectType.FILE;
  }
  static getFileIcon(file: FileObject): string {
    if (file.objType === FileObjectType.FOLDER) return 'folder';

    switch (file.type) {
      case FileExt.TYPE_MOVIE: return 'movie';
      case FileExt.TYPE_MUSIC: return 'music_note';
      case FileExt.TYPE_PICTURE: return 'insert_photo';
      case FileExt.TYPE_CODE: return 'code';
      case FileExt.TYPE_COMPRESSED: return 'archive';
      case FileExt.TYPE_EXECUTABLE: return 'apps';
      case FileExt.TYPE_LIBRARY: return 'integration_instructions';
      case FileExt.TYPE_BOOK: return 'book';
      default: return 'insert_drive_file';
    }
  }
}

@Component({
  selector: 'app-folder',
  templateUrl: './folder.component.html',
  styleUrls: ['./folder.component.scss']
})
export class FolderComponent implements OnInit, OnDestroy {
  mobileQuery: MediaQueryList;
  private _mobileQueryListener: any;
  private updateTimer: any;
  @ViewChild(MatSidenav) snav: MatSidenav;

  storageProviders: StorageProvider[] = [];
  jobs: Job[] = [];
  loadingCount: number = 0;
  folderId: string = '';
  searchText: string = '';

  constructor(private service: CommonService,
    private router: Router,
    private route: ActivatedRoute,
    private titleService: Title,
    private dialog: MatDialog,
    private media: MediaMatcher,
    private changeDetectorRef: ChangeDetectorRef) {

    this.titleService.setTitle('File Explorer - RPi Drive');
    // Responsive sidenav
    this.mobileQuery = this.media.matchMedia('(max-width: 600px)');
    this._mobileQueryListener = () => this.changeDetectorRef.detectChanges();
    this.mobileQuery.addEventListener('change', this._mobileQueryListener);
  }

  ngOnInit(): void {
    this.loadStorageProviders();
    this.checkAndLoadFolder();
    this.router.events.subscribe((value) => this.checkAndLoadFolder());
    this.loadJobs();
    this.updateTimer = interval(10 * 1000).subscribe(t => {
      this.loadJobs();
    }) // 10 seconds.
  }

  ngOnDestroy(): void {
    this.mobileQuery.removeEventListener('change', this._mobileQueryListener);
    this.updateTimer.unsubscribe();
  }

  closeSideNavIfNeeded(): void {
    if (this.mobileQuery.matches && this.snav) this.snav.close();
  }

  loadStorageProviders(): void {
    this.loadingCount++;
    this.service.getStorageProviders().subscribe((data: GetStorageProvidersResponse) => {
      this.storageProviders = data.values;
    }).add(() => {
      this.loadingCount--;
    });
  }

  loadStorageProvidersPage(): void {
    this.closeSideNavIfNeeded();
    this.router.navigateByUrl(Url.getFolderAbsURL());
  }

  loadStorageProviderFolder(storageProvider: StorageProvider) {
    this.closeSideNavIfNeeded();
    this.router.navigate([storageProvider.rootFolder], { relativeTo: this.route });
  }

  loadJobs(): void {
    this.service.getJobs().subscribe((data: GetJobsResponse) => {
      this.jobs = data.values;
    });
  }

  createStorageProvider(): void {
    this.closeSideNavIfNeeded();
    const diagRef = this.dialog.open(DialogEditStorageProviderComponent, {
      disableClose: true,
      data: null
    });
    diagRef.afterClosed().subscribe((data) => {
      if (data) window.location.reload();
    });
  }

  checkAndLoadFolder(): void {
    this.folderId = this.route.firstChild?.snapshot.params['folderid'];
    if (this.folderId === 'search') {
      this.searchText = this.route.snapshot.queryParams['keyword'];
    }
  }

  createFolder(): void {
    this.closeSideNavIfNeeded();
    const dialogRef = this.dialog.open(DialogCreateFolderComponent, {
      disableClose: true,
      data: this.folderId
    });
    dialogRef.afterClosed().subscribe((data: FileObject) => {
      if (data) {
        this.router.navigateByUrl('/', { skipLocationChange: true }).then(() =>
          this.router.navigate([Url.getSpecificFolderAbsURL(data.id)])
        );
      }
    });
  }

  fileUpload(): void {
    this.closeSideNavIfNeeded();
    const dialogRef = this.dialog.open(DialogFileUploadComponent, {
      disableClose: true,
      data: this.folderId
    });
    dialogRef.afterClosed().subscribe((data: number) => {
      if (data > 0) {
        this.router.navigateByUrl('/', { skipLocationChange: true }).then(() =>
          this.router.navigate([Url.getSpecificFolderAbsURL(this.folderId)])
        );
      }
    });
  }

  folderUpload(): void {
    this.closeSideNavIfNeeded();
    const dialogRef = this.dialog.open(DialogFolderUploadComponent, {
      disableClose: true,
      data: this.folderId
    });
    dialogRef.afterClosed().subscribe((data: number) => {
      if (data > 0) {
        this.router.navigateByUrl('/', { skipLocationChange: true }).then(() =>
          this.router.navigate([Url.getSpecificFolderAbsURL(this.folderId)])
        );
      }
    });
  }

  search() {
    this.closeSideNavIfNeeded();
    this.folderId = 'search';
    this.router.navigate([Url.getSearchAbsURL()], {
      queryParams: {'keyword': this.searchText}
    });
  }
}

@Component({
  selector: 'app-storage-provider-table',
  templateUrl: './storage-provider/table.component.html',
  styleUrls: ['./storage-provider/table.component.scss']
})
export class StorageProviderTableComponent implements AfterViewInit {
  @Input() storageProviders: StorageProvider[];
  @Input() isMobile: boolean;

  displayedColumns: string[] = ['name', 'path', 'usedSpace', 'totalSpace', 'indexing'];
  dataSource: MatTableDataSource<StorageProvider>;

  @ViewChild(MatSort) sort: MatSort;

  @ViewChild('spMenuTrigger', {read: MatMenuTrigger}) contextMenu: MatMenuTrigger;
  contextMenuPosition = { x: '0px', y: '0px' };

  constructor(private service: CommonService,
    private router: Router,
    private route: ActivatedRoute,
    private snackBar: MatSnackBar,
    private dialog: MatDialog) {
    this.dataSource = new MatTableDataSource(this.storageProviders);
  }

  ngOnChanges(changes: SimpleChanges) {
    this.dataSource.data = this.storageProviders;
  }

  ngAfterViewInit() {
    this.dataSource.sort = this.sort;
  }

  loadStorageProviderFolder(storageProvider: StorageProvider) {
    this.router.navigate([storageProvider.rootFolder], { relativeTo: this.route });
  }

  performIndex(storageProvider: StorageProvider) {
    this.service.storageProviderPerformIndex(storageProvider.id).subscribe(() => {
      this.snackBar.open('Indexing started on ' + storageProvider.name + '.',
        'Close',
        { duration: 3000 });
      storageProvider.indexing = true;
    }, error => {
      this.snackBar.open(error.error['error'],
        'Close',
        { duration: 3000 });
    })
  }

  onContextMenu(event: MouseEvent, item: StorageProvider) {
    event.preventDefault();
    this.contextMenuPosition.x = event.clientX + 'px';
    this.contextMenuPosition.y = event.clientY + 'px';
    this.contextMenu.menuData = { 'item': item };
    this.contextMenu.menu.focusFirstItem('mouse');
    this.contextMenu.openMenu();
  }

  editStorageProvider(storageProvider: StorageProvider): void {
    const diagRef = this.dialog.open(DialogEditStorageProviderComponent, {
      disableClose: true,
      data: storageProvider
    });
    diagRef.afterClosed().subscribe((data) => {
      if (data) window.location.reload();
    });
  }

  editStorageProviderPermissions(storageProvider: StorageProvider): void {
    const diagRef = this.dialog.open(DialogStorageProviderPermissionsComponent, {
      disableClose: true,
      data: storageProvider
    });
  }

  deleteStorageProvider(storageProvider: StorageProvider): void {
    const diagRef = this.dialog.open(DialogDeleteStorageProviderComponent, {
      disableClose: true,
      data: storageProvider
    });
    diagRef.afterClosed().subscribe((data) => {
      if (data) window.location.reload();
    });
  }
}


@Component({
  selector: 'dialog-storage-provider-edit',
  templateUrl: './storage-provider/edit.component.html'
})
export class DialogEditStorageProviderComponent {
  loading: boolean = false;
  errorText: string;
  formGroup: UntypedFormGroup;

  storageProviderTypes: StorageProviderType[];

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogEditStorageProviderComponent>,
    @Inject(MAT_DIALOG_DATA) public storageProvider: StorageProvider,
    private formBuilder: UntypedFormBuilder,
    private snackBar: MatSnackBar) {

    this.loading = true;
    this.service.getStorageProviderTypes().subscribe((data: GetStorageProviderTypesResponse) => {
      this.storageProviderTypes = data.values;
      this.formGroup = this.formBuilder.group({
        name: new UntypedFormControl(storageProvider ? storageProvider.name : '', Validators.required),
        type: new UntypedFormControl(storageProvider ? storageProvider.type : '', Validators.required),
        path: new UntypedFormControl(storageProvider ? storageProvider.path : '', Validators.required)
      })
    }).add(() => {
      this.loading = false;
    })

  }

  createOrUpdateStorageProvider() {
    this.loading = true;
    this.errorText = '';

    let sp = new StorageProvider();
    sp.name = this.formGroup.get('name').value;
    sp.type = this.formGroup.get('type').value;
    sp.path = this.formGroup.get('path').value;

    if (!this.storageProvider) {
      this.service.createStorageProvider(sp).subscribe((data: StorageProvider) => {
        this.snackBar.open('Storage provider is created.', 'Close', { duration: 3000 });
        this.dialogRef.close(data);
      }, error => {
        this.errorText = error.error['error'];
      }).add(() => this.loading = false);
    } else {
      sp.id = this.storageProvider.id;
      this.service.updateStorageProvider(sp).subscribe((data: StorageProvider) => {
        this.snackBar.open('Storage provider is updated.', 'Close', { duration: 3000 });
        this.dialogRef.close(data);
      }, error => {
        this.errorText = error.error['error'];
      }).add(() => this.loading = false);
    }
  }

}

@Component({
  selector: 'dialog-storage-provider-permissions',
  templateUrl: './storage-provider/permissions.component.html'
})
export class DialogStorageProviderPermissionsComponent {
  loadingLevel: number = 0;
  initialDataErrorText: string;
  errorText: string;

  selectedUser: User = null;
  users: User[];
  spPermissions: StorageProviderPermission[];

  permissionTableDataSource: MatTableDataSource<StorageProviderUser>;
  permissionTableDisplayedColumns: string[] = ['username', 'permission'];

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogStorageProviderPermissionsComponent>,
    @Inject(MAT_DIALOG_DATA) public storageProvider: StorageProvider,
    private snackBar: MatSnackBar) {
      this.permissionTableDataSource = new MatTableDataSource();
      this.loadInitialData();
  }

  loadInitialData() {
    this.loadingLevel++;
    this.service.getUsers().subscribe((response : GetUsersResponse) => {
      this.users = response.values;
    }, error => {
      this.initialDataErrorText = error.error['error'];
    }).add(() => this.loadingLevel--);

    this.loadingLevel++;
    this.service.getStorageProviderPermissions().subscribe((response : GetStorageProviderPermissionsResponse) => {
      this.spPermissions = response.values;
    }, error => {
      this.initialDataErrorText = error.error['error'];
    }).add(() => this.loadingLevel--);

    this.loadingLevel++;
    this.service.getStorageProvider(this.storageProvider.id, true).subscribe((response : StorageProvider) => {
      this.storageProvider = response;
      this.updateTable();
    }, error => {
      this.initialDataErrorText = error.error['error'];
    }).add(() => this.loadingLevel--);
  }

  userExistsInPermissions(user: User) {
    for (let p of this.storageProvider.permissions) if (p.user.id === user.id) return true;
    return false;
  }

  updateTable() {
    this.permissionTableDataSource.data = this.storageProvider.permissions;
  }

  addPermission(user: User) {
    this.selectedUser = null;

    let p = new StorageProviderUser();
    p.user = user;
    p.permission = this.spPermissions[0].value;
    this.storageProvider.permissions.push(p);
    this.updateTable();
  }

  removePermission(perm : StorageProviderUser) {
    this.storageProvider.permissions = this.storageProvider.permissions.filter(x => x!=perm);
    this.updateTable();
  }

  savePermissions() {
    this.loadingLevel++;
    this.errorText = null;
    this.service.updateStorageProviderPermissions(this.storageProvider).subscribe((response: StorageProvider) => {
      this.snackBar.open('Permission updated successfully', 'Close', {
        duration: 3000
      });
      this.dialogRef.close();
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => this.loadingLevel-- );
  }
}

@Component({
  selector: 'dialog-storage-provider-delete',
  templateUrl: './storage-provider/delete.component.html'
})
export class DialogDeleteStorageProviderComponent {
  loading: boolean = false;
  errorText: string;

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogDeleteStorageProviderComponent>,
    @Inject(MAT_DIALOG_DATA) public storageProvider: StorageProvider,
    private snackBar: MatSnackBar) {
  }

  deleteStorageProvider() {
    this.loading = true;
    this.errorText = '';
    this.service.deleteStorageProvider(this.storageProvider.id).subscribe(() => {
      this.dialogRef.close(1);
      this.snackBar.open('Storage provider ' + this.storageProvider.name + ' is deleted.', 'Close', { duration: 3000 });
    }, error => {
      this.errorText = error.error['error']
    }).add(() => this.loading = false);
  }
}

@Component({
  selector: 'app-search-table',
  templateUrl: './search/table.component.html',
  styleUrls: ['./search/table.component.scss']
})
export class SearchTableComponent implements OnDestroy {
  @Input() keyword: string;
  @Input() isMobile: boolean;

  loading: boolean = false;
  displayedColumns: string[] = ['name', 'path', 'lastModified', 'size'];
  dataSource: MatTableDataSource<FileObject>;
  @ViewChild(MatSort, { static: false }) set sort(_sort: MatSort) {
    this.dataSource.sort = _sort;
  }
  changeDebounced: EventEmitter<string>

  constructor(private service: CommonService,
    private router: Router,
    private route: ActivatedRoute,
    private dialog: MatDialog) {
      this.dataSource = new MatTableDataSource();
      this.changeDebounced = new EventEmitter<string>();
      this.changeDebounced.pipe(
        debounceTime(500),
        distinctUntilChanged(),
        tap((text) => {
          this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {
              'keyword': text
            }
          });
          if (text) this.search();
          else this.dataSource.data = [];
        })
      ).subscribe();
  }

  ngOnChanges(changes: SimpleChanges) {
    this.changeDebounced.emit(this.keyword);
  }

  ngOnDestroy() {
    this.changeDebounced.unsubscribe();
  }

  search() {
    this.loading = true;
    this.service.searchFile(this.keyword).subscribe((data : SearchResultResponse) => {
      this.dataSource.data = data.values;
    }).add(() => {
      this.loading = false;
    });
  }

  getFileIcon(file: FileObject): string {
    return Utils.getFileIcon(file);
  }

  isFile(file: FileObject): boolean {
    return Utils.isFile(file);
  }

  loadFileObject(file: FileObject) {
    if (file.objType === FileObjectType.FOLDER) {
      this.router.navigate([file.id], { relativeTo: this.route });
    } else if (file.objType == FileObjectType.FILE) {
      this.previewOrDownload(file);
    }
  }

  previewOrDownload(file: FileObject) {
    if (FilePreviewType.getFilePreviewType(file.extension)) {
      this.dialog.open(DialogFilePreviewComponent, {
        data: file
      });
    } else this.service.downloadFile(file.id);
  }
}

@Component({
  selector: 'app-folder-table',
  templateUrl: './folder/table.component.html',
  styleUrls: ['./folder/table.component.scss']
})
export class FolderTableComponent {
  @Input() folderId: string;
  @Input() isMobile: boolean;
  
  loading: boolean = false;
  errorText: string;
  folder: FileObject;

  displayedColumns: string[] = ['selection', 'name', 'lastModified', 'size'];
  dataSource: MatTableDataSource<FileObject>;
  @ViewChild(MatSort, { static: false }) set sort(_sort: MatSort) {
    this.dataSource.sort = _sort;
  }

  selection = new SelectionModel<FileObject>(true, []);

  @ViewChild('fileOpMenu', {read: MatMenuTrigger}) contextMenu: MatMenuTrigger;
  contextMenuPosition = { x: '0px', y: '0px' };

  constructor(private service: CommonService,
    private dialog: MatDialog,
    private router: Router,
    private route: ActivatedRoute) {
    this.dataSource = new MatTableDataSource();
  }

  onContextMenu(event: MouseEvent, item: FileObject) {
    this.selection.clear();

    event.preventDefault();
    this.contextMenuPosition.x = event.clientX + 'px';
    this.contextMenuPosition.y = event.clientY + 'px';
    this.contextMenu.menuData = { 'item': item };
    this.contextMenu.menu.focusFirstItem('mouse');
    this.contextMenu.openMenu();
  }

  ngOnChanges(changes: SimpleChanges) {
    this.loadCurrentFolder();
  }

  loadCurrentFolder() {
    this.loading = true;
    this.errorText = '';
    this.dataSource.data = [];
    this.selection.clear();
    this.service.getFolder(this.folderId).subscribe((folder: FileObject) => {
      this.folder = folder;
      this.dataSource.data = folder.children;
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => {
      this.loading = false;
    })
  }

  loadFileObject(file: FileObject) {
    if (file.objType === FileObjectType.FOLDER) {
      this.router.navigate([file.id], { relativeTo: this.route });
    } else if (file.objType == FileObjectType.FILE) {
      this.previewOrDownload(file);
    }
  }

  loadParentFolder() {
    if (this.folder.parent) {
      this.router.navigate([this.folder.parent.id], { relativeTo: this.route });
    }
  }

  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.length;
    return numSelected === numRows;
  }

  masterToggle() {
    this.isAllSelected() ?
      this.selection.clear() :
      this.dataSource.data.forEach(row => this.selection.select(row));
    this.onSelectionChange(null, null);
  }

  checkboxLabel(row?: FileObject): string {
    if (!row) {
      return `${this.isAllSelected() ? 'select' : 'deselect'} all`;
    }
    return `${this.selection.isSelected(row) ? 'deselect' : 'select'} row ${row['position'] + 1}`;
  }

  onSelectionChange(selection: SelectionModel<FileObject>, row: FileObject) {
    if (selection != null) selection.toggle(row);

    let selectList: Object[] = [];
    for (let f of this.selection.selected) selectList.push(f);
  }

  getFileIcon(file: FileObject): string {
    return Utils.getFileIcon(file);
  }

  isFile(file: FileObject): boolean {
    return Utils.isFile(file);
  }

  previewOrDownload(file: FileObject) {
    if (FilePreviewType.getFilePreviewType(file.extension)) {
      this.dialog.open(DialogFilePreviewComponent, {
        data: file
      });
    } else this.service.downloadFile(file.id);
  }

  shareSelectedFile(file: FileObject | null) {
    const dialogRef = this.dialog.open(DialogShareFileComponent, {
      data: file ? file : this.selection.selected[0]
    });
  }

  zipSelectedFiles(file: FileObject | null) {
    const dialogRef = this.dialog.open(DialogZipFileComponent, {
      data: {
        files: file ? [file] : this.selection.selected,
        destination: this.folder,
      }
    });
  }

  renameSelectedFile(file: FileObject | null) {
    const dialogRef = this.dialog.open(DialogRenameFileComponent, {
      disableClose: true,
      data: file ? file : this.selection.selected[0]
    });
    dialogRef.afterClosed().subscribe((data: any) => {
      if (data) this.loadCurrentFolder();
    })
  }

  moveSelectedFiles(file: FileObject | null) {
    const dialogRef = this.dialog.open(DialogMoveFileComponent, {
      disableClose: true,
      data: file ? [file] : this.selection.selected
    });
    dialogRef.afterClosed().subscribe((data: any) => {
      if (data) this.loadCurrentFolder();
    })
  }

  deleteSelectedFiles(file: FileObject | null) {
    const dialogRef = this.dialog.open(DialogDeleteFileComponent, {
      disableClose: true,
      data: file ? [file] : this.selection.selected
    });
    dialogRef.afterClosed().subscribe((data: any) => {
      if (data) this.loadCurrentFolder();
    })
  }
}

@Component({
  selector: 'dialog-create-folder',
  templateUrl: './folder/create-folder.component.html',
})
export class DialogCreateFolderComponent {
  loading: boolean = false;
  errorText: string;
  formControl: UntypedFormControl;

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogCreateFolderComponent>,
    private router: Router,
    private route: ActivatedRoute,
    @Inject(MAT_DIALOG_DATA) public folderId: string,
  ) {
    this.formControl = new UntypedFormControl('', Validators.required);
  }

  createFolder() {
    let folderName = this.formControl.value;
    this.loading = true;
    this.errorText = '';
    this.service.createFolder(this.folderId, folderName).subscribe((createdFolder: FileObject) => {
      this.dialogRef.close(createdFolder);
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => {
      this.loading = false;
    })
  }
}

@Component({
  selector: 'dialog-file-upload',
  templateUrl: './folder/file-upload.component.html',
  styleUrls: ['./folder/file-upload.component.scss'],
  animations: [
        trigger('fadeInOut', [
              state('in', style({ opacity: 100 })),
              transition('* => void', [
                    animate(300, style({ opacity: 0 }))
              ])
        ])
  ]
})
export class DialogFileUploadComponent {
  @Output() complete = new EventEmitter<string>();
  files: Array<FileUploadModel> = [];
  uploadCount: number = 0;
  uploadSuccess: number = 0;
  successList: string[] = [];

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogFileUploadComponent>,
    @Inject(MAT_DIALOG_DATA) public folderId: string) {
  }

  onClick() {
    const fileUpload = document.getElementById('fileUpload') as HTMLInputElement;
    fileUpload.onchange = () => {
      for (let i = 0; i < fileUpload.files.length; i++) this.files.push({ data: fileUpload.files[i], state: 'in', inProgress: false, progress: 0, canRetry: false, canCancel: true });
      this.uploadFiles();
    };
    fileUpload.click();
  }

  cancelFile(file: FileUploadModel) {
    file.sub.unsubscribe();
    this.removeFileFromArray(file);
    this.uploadCount--;
  }

  retryFile(file: FileUploadModel) {
    this.uploadFile(file);
    file.canRetry = false;
  }

  private uploadFile(file: FileUploadModel) {
    const fd = new FormData();
    fd.append('files', file.data);
    fd.append('paths', file.data.webkitRelativePath);

    this.uploadCount++;
    file.inProgress = true;
    file.sub = this.service.uploadFiles(this.folderId, fd).pipe(
      map(event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            file.progress = Math.round(event.loaded * 100 / event.total);
            break;
          case HttpEventType.Response:
            return event;
        }
      }),
      tap(message => { }),
      last(),
      catchError((error: HttpErrorResponse) => {
        file.inProgress = false;
        file.canRetry = true;
        this.uploadCount--;
        return of(`${file.data.name} upload failed.`);
      })
    ).subscribe(
      (event: any) => {
        this.removeFileFromArray(file);
        this.uploadCount--;
        this.uploadSuccess++;
        this.successList.push(file.data.name);
        if (event) this.complete.emit(event.body);
      }
    );
  }

  private uploadFiles() {
    const fileUpload = document.getElementById('fileUpload') as HTMLInputElement;
    fileUpload.value = '';
    this.files.forEach(file => this.uploadFile(file));
  }

  private removeFileFromArray(file: FileUploadModel) {
    const index = this.files.indexOf(file);
    if (index > -1) this.files.splice(index, 1);
  }

  onCloseClick(): void {
    this.dialogRef.close(this.uploadSuccess);
  }

}

@Component({
  selector: 'dialog-folder-upload',
  templateUrl: './folder/folder-upload.component.html',
})
export class DialogFolderUploadComponent {
  @Output() complete = new EventEmitter<string>();
  files: Array<FileUploadModel> = [];
  uploadCount: number = 0;
  uploadSuccess: number = 0;
  successList: string[] = [];

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogFolderUploadComponent>,
    @Inject(MAT_DIALOG_DATA) public folderId: string) {
  }

  onSelectFolder() {
    const folderUpload = document.getElementById('folderUpload') as HTMLInputElement;
    folderUpload.onchange = () => {
      for (let i = 0; i < folderUpload.files.length; i++) this.files.push({ data: folderUpload.files[i], state: 'in', inProgress: false, progress: 0, canRetry: false, canCancel: true });
      this.uploadFiles();
    };
    folderUpload.click();
  }

  private removeFileFromArray(file: FileUploadModel) {
    const index = this.files.indexOf(file);
    if (index > -1) this.files.splice(index, 1);
  }

  private uploadFile(file: FileUploadModel) {
    const fd = new FormData();
    fd.append('files', file.data);
    fd.append('paths', file.data.webkitRelativePath);

    this.uploadCount++;
    file.inProgress = true;
    file.sub = this.service.uploadFiles(this.folderId, fd).pipe(
      map(event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            file.progress = Math.round(event.loaded * 100 / event.total);
            break;
          case HttpEventType.Response:
            return event;
        }
      }),
      tap(message => { }),
      last(),
      catchError((error: HttpErrorResponse) => {
        file.inProgress = false;
        file.canRetry = true;
        this.uploadCount--;
        return of(`${file.data.webkitRelativePath} upload failed.`);
      })
    ).subscribe(
      (event: any) => {
        this.removeFileFromArray(file);
        this.uploadCount--;
        this.uploadSuccess++;
        this.successList.push(file.data.webkitRelativePath);
        if (event) this.complete.emit(event.body);
      }
    );
  }

  private uploadFiles() {
    const folderUpload = document.getElementById('folderUpload') as HTMLInputElement;
    folderUpload.value = '';
    this.files.forEach(file => this.uploadFile(file));
  }

  cancelFile(file: FileUploadModel) {
    file.sub.unsubscribe();
    this.removeFileFromArray(file);
    this.uploadCount--;
  }

  retryFile(file: FileUploadModel) {
    this.uploadFile(file);
    file.canRetry = false;
  }

  onCloseClick(): void {
    this.dialogRef.close(this.uploadSuccess);
  }
}

@Component({
  selector: 'dialog-file-preview',
  templateUrl: './folder/file-preview.component.html',
  styleUrls: ['./folder/file-preview.component.scss'],
})
export class DialogFilePreviewComponent {
  codeContent: string;
  metadata: Metadata;
 
  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogFilePreviewComponent>,
    @Inject(MAT_DIALOG_DATA) public file: FileObject) {
      this.service.getFileMetadata(file.id).subscribe((data: Metadata) => {
        this.metadata = data;
      })
      if (this.getFilePreviewType() === FilePreviewType.CODE) {
        this.service.getFileContent(file.id).subscribe((data: string) => {
          this.codeContent = data;
        })
      }
  }

  getFileUrl() {
    return this.service.getFileDownloadUrl(this.file.id);
  }

  getFileIcon() {
    return Utils.getFileIcon(this.file);
  }

  getFilePreviewType() {
    return FilePreviewType.getFilePreviewType(this.file.extension);
  }

  getAlbumArtUrl() {
    return (this.getFilePreviewType() === FilePreviewType.MUSIC) ? this.service.getMusicAlbumImageUrl(this.file.id) : '';
  }
  
  downloadFile() {
    this.service.downloadFile(this.file.id);
  }
}


@Component({
  selector: 'dialog-delete-file',
  templateUrl: './folder/delete.component.html',
})
export class DialogDeleteFileComponent {
  loadingLevel: number = 0;
  deleteSuccess: number = 0;
  filesToDelete: FileObject[] = [];
  errorText: string;

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogCreateFolderComponent>,
    @Inject(MAT_DIALOG_DATA) public files: FileObject[],
    private snackBar: MatSnackBar) {
  }

  private deleteFileHelper() {
    if (this.filesToDelete.length > 0) {
      this.loadingLevel++;
      let lastIdx = this.filesToDelete.length - 1;
      this.service.deleteFile(this.filesToDelete[lastIdx].id).subscribe(() => {
        this.deleteSuccess++;
      }, error => {
        this.errorText = this.filesToDelete[lastIdx].name + ' error :' + error.error['error'];
      }).add(() => {
        this.loadingLevel--;
        this.filesToDelete.pop();
        this.deleteFileHelper();
      });
    } else {
      if (!this.errorText) this.dialogRef.close(this.deleteSuccess);
    }
  }

  deleteFile() {
    this.errorText = null;
    for (let file of this.files) this.filesToDelete.push(file);
    this.deleteFileHelper();
  }
}

@Component({
  selector: 'dialog-move-file',
  templateUrl: './folder/move.component.html',
  styleUrls: ['./folder/move.component.scss']
})
export class DialogMoveFileComponent {
  loadingLevel: number = 0;
  errorText: string;

  storageProviders: StorageProvider[];
  folders: FileObject[];

  currStorageProvider: StorageProvider;
  currFolder: FileObject;

  successCount: number = 0;
  strategy: string = 'rename';

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogCreateFolderComponent>,
    @Inject(MAT_DIALOG_DATA) public files: FileObject[],
    private snackBar: MatSnackBar) {
    this.loadingLevel++;
    this.service.getStorageProviders().subscribe((data: GetStorageProvidersResponse) => {
      this.storageProviders = data.values;
    }).add(() => this.loadingLevel--);
  }

  selectStorageProvider(storageProvider: StorageProvider) {
    this.currStorageProvider = storageProvider;
    this.loadFolder(this.currStorageProvider.rootFolder);
  }

  loadFolder(folderId: string) {
    this.loadingLevel++;
    this.service.getFolder(folderId).subscribe((data: FileObject) => {
      this.currFolder = data;
    }).add(() => this.loadingLevel--);
  }

  goToParent() {
    if (this.currFolder.parent) this.loadFolder(this.currFolder.parent.id);
    else this.currFolder = null;
  }

  moveFile() {
    this.errorText = '';
    const filesToMoveId = this.files.map(x => x.id)
    this.loadingLevel++;
    this.service.moveFile(filesToMoveId, this.currFolder.id, this.strategy).subscribe(() => {
      this.successCount++;
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => {
      this.loadingLevel--
      if (this.loadingLevel == 0 && !this.errorText) {
        this.snackBar.open('File(s) are moved.', 'Close', { duration: 3000 });
        this.dialogRef.close(this.successCount);
      }
    });
  }

  filterBlockFolder(children: FileObject[]) {
    let ids = this.files.map(x => x.id);
    return children.filter(x => !ids.includes(x.id) && x.objType === FileObjectType.FOLDER);
  }
}

@Component({
  selector: 'dialog-zip-file',
  templateUrl: './folder/zip-file.component.html',
})
export class DialogZipFileComponent {
  static InputSchema = class{
    files: FileObject[];
    destination: FileObject;
  }

  loading: boolean = false;
  errorText: string;
  formControl: UntypedFormControl;

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogZipFileComponent>,
    @Inject(MAT_DIALOG_DATA) public data: typeof DialogZipFileComponent.InputSchema.prototype,
    private snackBar: MatSnackBar
  ) {
    if (this.data.files.length == 1) {
      this.formControl = new UntypedFormControl(this.data.files[0].name, Validators.required);
    } else {
      this.formControl = new UntypedFormControl(this.data.destination.name, Validators.required);
    }
  }

  zipFile() {
    let name = this.formControl.value;
    this.loading = true;
    this.errorText = '';

    const files = this.data.files.map(x => x.id)
    this.service.zipFiles(files, this.data.destination.id, name).subscribe(() => {
      this.snackBar.open('Zip file job created.', 'Close', { duration: 3000 });
      this.dialogRef.close();
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => {
      this.loading = false;
    });
  }

}

@Component({
  selector: 'dialog-rename-file',
  templateUrl: './folder/rename.component.html',
})
export class DialogRenameFileComponent {
  loading: boolean = false;
  errorText: string;
  formControl: UntypedFormControl;

  constructor(private service: CommonService,
    private dialogRef: MatDialogRef<DialogRenameFileComponent>,
    @Inject(MAT_DIALOG_DATA) public file: FileObject,
    private snackBar: MatSnackBar) {
    this.formControl = new UntypedFormControl(file.name, Validators.required);
  }

  renameFile() {
    let name = this.formControl.value;
    this.loading = true;
    this.errorText = '';
    this.service.renameFile(this.file.id, name).subscribe(() => {
      this.snackBar.open(this.file.name + ' is renamed to ' + name + '.', 'Close', { duration: 3000 });
      this.file.name = name;
      this.dialogRef.close(1);
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => {
      this.loading = false;
    });
  }

}

@Component({
  selector: 'dialog-share-file',
  templateUrl: './folder/share.component.html',
})
export class DialogShareFileComponent {
  loading: boolean = false;
  errorText: string;
  shareUrl: string;
  canQuickAccess: boolean;
  quickAccessUrl: string;

  constructor(private service: CommonService,
    @Inject(MAT_DIALOG_DATA) public file: FileObject) {
      this.canQuickAccess = this.file.objType === FileObjectType.FILE;
      this.shareUrl = this.getFileUrl();
  }

  getFileUrl() {
    if (this.file.objType === FileObjectType.FILE) {
      return window.location.origin +
        this.service.getFileDownloadUrl(this.file.id);
    }
    return window.location.origin +
      Url.getSpecificFolderAbsURL(this.file.id);
  }

  generateQuickAccessKey() {
    this.service.generateQuickAccessKey(this.file.id).subscribe((data: GenerateQuickAccessKeyResponse) => {
      this.quickAccessUrl = window.location.origin +
        this.service.getFileQuickAccessUrl(data.key);
    });
  }
}