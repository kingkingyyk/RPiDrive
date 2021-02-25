import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { MediaMatcher } from '@angular/cdk/layout';
import { ChangeDetectorRef, Component, Inject, Injectable, Input, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatMenuTrigger } from '@angular/material/menu';
import { MatSidenav } from '@angular/material/sidenav';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { BehaviorSubject, Subscription } from 'rxjs';
import { CommonService } from 'src/app/services/common.service';
import { FileExt, FileObject, FileObjectType, GetPlaylistsResponse, GetStorageProvidersResponse, Playlist, StorageProvider, FilePreviewType, Metadata } from '../models';
import { Url } from '../urls';

@Component({
  selector: 'app-media-player',
  templateUrl: './media-player.component.html',
  styleUrls: ['./media-player.component.scss']
})
export class MediaPlayerComponent implements OnInit {
  mobileQuery: MediaQueryList;
  private _mobileQueryListener: any;
  @ViewChild('snav') snav: MatSidenav;

  playlists: Playlist[];
  uiSelectedPlaylist: Playlist[] = [];
  selectedPlaylist: Playlist;

  loadingPlaylists: boolean = false;

  constructor(private service: CommonService,
              private dialog: MatDialog,
              private router: Router,
              private route: ActivatedRoute,
              private titleService: Title,
              private media: MediaMatcher,
              private changeDetectorRef: ChangeDetectorRef) {
          
              // Responsive sidenav
              this.mobileQuery = this.media.matchMedia('(max-width: 600px)');
              this._mobileQueryListener = () => this.changeDetectorRef.detectChanges();
              this.mobileQuery.addEventListener('change', this._mobileQueryListener);
              }

  ngOnInit(): void {
    this.titleService.setTitle('Media Player - RPi Drive');
    this.loadPlaylists();

    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        if (event['url'] === '/'+Url.getMediaPlayerAbsUrl()) {
          this.uiSelectedPlaylist = [];
          this.selectedPlaylist = null;
        }
      }
    });
  }

  loadPlaylists(): void {
    this.loadingPlaylists = true;
    this.service.getPlaylists().subscribe((data: GetPlaylistsResponse) => {
      this.playlists = data.values;
    }).add(() => {
      this.loadingPlaylists = false;
      let plid = this.route.firstChild?.snapshot.params['playlistid'];
      if (plid) {
        plid = parseInt(plid);
        for (let pl of this.playlists) if (pl.id === plid) {
          this.uiSelectedPlaylist = [pl];
          this.selectedPlaylist = pl;
        }
      } else {
        this.uiSelectedPlaylist = [];
        this.selectedPlaylist = null;
      }
    });
  }

  createPlaylist(): void {
    const dialogRef = this.dialog.open(DialogCreatePlaylistComponent, {
      disableClose: true
    });
    dialogRef.afterClosed().subscribe((data: Playlist) => {
      if (data) {
        this.playlists.push(data);
        this.playlists.sort((a, b) => {return a.name.localeCompare(b.name)});
        this.uiSelectedPlaylist = [data];
        this.uiOnSelectPlaylist();
      }
    });
  }

  uiOnSelectPlaylist(): void {
    this.selectedPlaylist = this.uiSelectedPlaylist[0];
    this.router.navigateByUrl(Url.getMediaPlayerPlaylistAbsUrl(this.selectedPlaylist.id));
    this.closeSideNavIfNeeded();
  }

  @ViewChild('fileBrowser', {static: false}) fileBrowser: MatSidenav;
  
  closeSideNavIfNeeded(): void {
    if (this.mobileQuery.matches && this.snav) this.snav.close();
  }
}

@Component({
  selector: 'dialog-create-playlist',
  templateUrl: './create-playlist.component.html',
})
export class DialogCreatePlaylistComponent {
  loading: boolean = false;
  errorText: string;
  formControl: FormControl;

  constructor(private service: CommonService,
    @Inject(MAT_DIALOG_DATA) public playlist: Playlist,
    private dialogRef: MatDialogRef<DialogCreatePlaylistComponent>) {
    this.formControl = new FormControl(playlist ? playlist.name: '', Validators.required);
  }

  createOrUpdatePlaylist() {
    let data = {name: this.formControl.value};
    this.loading = true;
    this.errorText = '';
    if (!this.playlist) {
      this.service.createPlaylist(data).subscribe((playlist: Playlist) => {
        this.dialogRef.close(playlist);
      }, error => {
        this.errorText = error.error['error'];
      }).add(() => {
        this.loading = false;
      })
    } else {
      this.service.savePlaylist(this.playlist.id, data).subscribe((playlist: Playlist) => {
        this.dialogRef.close(this.formControl.value);
      }, error => {
        this.errorText = error.error['error'];
      }).add(() => {
        this.loading = false;
      })
    }
  }
}

@Component({
  selector: 'dialog-delete-playlist',
  templateUrl: './delete-playlist.component.html'
})
export class DialogDeletePlaylistComponent {
  loading: boolean = false;
  errorText: string;

  constructor(private service: CommonService,
    @Inject(MAT_DIALOG_DATA) public playlist: Playlist,
    private dialogRef: MatDialogRef<DialogDeletePlaylistComponent>) {}

  deletePlaylist() {
    this.loading = true;
    this.errorText = '';
    this.service.deletePlaylist(this.playlist.id).subscribe((playlist: Playlist) => {
      this.dialogRef.close(1);
    }, error => {
      this.errorText = error.error['error'];
    }).add(() => {
      this.loading = false;
    })
  }
}

@Injectable({ providedIn: 'root' })
export class PlaylistAddFileService {
  private channel = new BehaviorSubject('');
  currentMessage = this.channel.asObservable();

  constructor() {}

  push(f : FileObject) {
    this.channel.next(f.id);
  }
}

@Component({
  selector: 'app-playlist-player',
  templateUrl: './playlist.component.html',
  styleUrls: ['./playlist.component.scss']
})
export class PlaylistComponent implements OnInit, OnDestroy {
  @Input() isMobile: boolean;

  loading: boolean = false;
  errorText: string;

  private _playlist: Playlist;
  private _i_playlist: Playlist;

  get playlist(): Playlist { return this._playlist; }
  @Input() set playlist(val: Playlist) {
    this._i_playlist = val;
    this.currentPlaying = null;
    this.loadPlaylist();
  }

  @Input() mediaPlayer: MediaPlayerComponent;
  addFileSrvSub: Subscription;

  constructor(private service: CommonService,
              private titleService: Title,
              private addFileSrv: PlaylistAddFileService,
              private router: Router,
              private dialog: MatDialog,
              private snackbar: MatSnackBar) {}

  // ================ ADD FILE ================
  ngOnInit() {
    this.addFileSrvSub = this.addFileSrv.currentMessage.subscribe((fid: string) => {
      if (fid && this.playlist) {
        if (!this.playlist.files) this.playlist.files = [];
        let temp = this.playlist.files.filter(x => x.id === fid);
        if (temp.length == 0) {
          this.service.getFile(fid).subscribe((file : FileObject) => {
            this.playlist.files.push(file);
            this.savePlaylist();
            this.snackbar.open(file.name+' is added!', 'Close', {
              duration: 3000
            });
          })
        } else {
          this.snackbar.open('Media is already added!', 'Close', {
            duration: 3000
          });
        }
      }
    });

    // Handle MediaSession UI (For OS/Browser-based control)
    let nav: any;
    nav = window.navigator;
    if (nav.mediaSession) {
      nav.mediaSession.setActionHandler('previoustrack', () => this.playPrevFile());
      nav.mediaSession.setActionHandler('nexttrack', () => this.playNextFile());
    }
  }

  ngOnDestroy() {
    this.addFileSrvSub.unsubscribe();
  }

  addFile() {
    this.mediaPlayer.fileBrowser.toggle();
  }

  // ============= MODIFY PLAYLIST ============
  loadPlaylist() {
    this.loading = true;
    this.service.getPlaylist(this._i_playlist.id).subscribe((pl: Playlist) => {
      this._playlist = pl;
      if (this.playlist.files.length > 0) this.playFile(this.playlist.files[0]);
    }).add(() => this.loading = false);
  }
  
  renamePlaylist() {
    const dialogRef = this.dialog.open(DialogCreatePlaylistComponent, {
      data: this.playlist,
      disableClose: true
    })
    dialogRef.afterClosed().subscribe((data) => {
      if (data) {
        this._playlist.name = data;
        this._i_playlist.name = data;
      }
    });
  }

  savePlaylist() {
    let ids = {files: this.playlist.files.map(x => x.id)};
    this.service.savePlaylist(this.playlist.id, ids).subscribe(() => {});
  }

  deletePlaylist() {
    const dialogRef = this.dialog.open(DialogDeletePlaylistComponent, {
      data: this.playlist,
      disableClose: true
    })
    dialogRef.afterClosed().subscribe((data) => {
      if (data) {
        this._playlist = null;
        this.router.navigateByUrl('/', {skipLocationChange: true}).then(() => {
          this.router.navigate([Url.getMediaPlayerAbsUrl()]);
      });
      }
    });
  }

  // ================ NOW PLAYING =====================
  currentPlaying: FileObject;

  playFile(f : FileObject) {
    this.currentPlaying = f;

    let nav: any;
    nav = window.navigator;
    if (nav.mediaSession) {
      nav.mediaSession.metadata = new MediaMetadata({
        title: this.currentPlaying.metadata.title ? this.currentPlaying.metadata.title : f.name,
        artist: this.currentPlaying.metadata.artist ? this.currentPlaying.metadata.artist: '',
        album: this.currentPlaying.metadata.album ? this.currentPlaying.metadata.album: '',
        artwork: [
          { src: this.getCurrentPlayingAlbumUrl() }
        ]
      });
    }

    this.titleService.setTitle(f.name+' - RPi Drive');
  }

  getCurrentPlayingUrl(): string {
    return this.service.getFileDownloadUrl(this.currentPlaying.id);
  }

  getCurrentPlayingIndex(): number {
    return this.playlist.files.indexOf(this.currentPlaying);
  }

  getCurrentPlayingAlbumUrl(): string {
    return this.service.getMusicAlbumImageUrl(this.currentPlaying.id)
  }

  playNextFile() {
    if (this.playlist.files.length > 0) {
      let idx = (this.getCurrentPlayingIndex()+1)%this.playlist.files.length;
      if (idx < 0 ) idx += this.playlist.files.length;
      this.playFile(this.playlist.files[idx]);
    } else this.currentPlaying = null;
  }

  playPrevFile() {
    if (this.playlist.files.length > 0) {
      let idx = (this.getCurrentPlayingIndex()-1)%this.playlist.files.length;
      this.playFile(this.playlist.files[idx]);
    } else this.currentPlaying = null;
  }

  reorderMedia(event: CdkDragDrop<string[]>) {
    moveItemInArray(this.playlist.files, event.previousIndex, event.currentIndex);
    this.savePlaylist();
  }

  deleteFileFromPlaylist(f: FileObject) {
    this.playlist.files = this.playlist.files.filter(x => x.id !== f.id);
    this.savePlaylist();
    if (this.currentPlaying && this.currentPlaying.id == f.id) this.playNextFile();
  }
}

@Component({
  selector: 'app-playlist-file-browser',
  templateUrl: './file-browser.component.html'
})
export class PlaylistFileBrowserComponent implements OnInit {
  loading: boolean = true;
  error: string = '';

  currFolder: FileObject;
  storageProviders: StorageProvider[];

  @Input() mediaPlayer: MediaPlayerComponent;

  constructor(private service: CommonService,
              private addFileSrv: PlaylistAddFileService,
              private snackbar: MatSnackBar) {}

  ngOnInit() {
    this.loadStorageProviders();
  }

  loadStorageProviders() {
    this.loading = true;
    this.service.getStorageProviders().subscribe((response : GetStorageProvidersResponse) => {
      this.storageProviders = response.values;
    }, error => {
      this.error = error.error['error']
    }).add(() => this.loading = false);
  }

  loadFolder(id: string) {
    this.loading = true;
    this.service.getFolder(id).subscribe((data: FileObject) => {
      data.children = data.children.filter((x : FileObject) => {
        return x.objType === FileObjectType.FOLDER || (
          x.objType === FileObjectType.FILE && (x.type === FileExt.TYPE_MOVIE || x.type === FileExt.TYPE_MUSIC)
        )
      });
      this.currFolder = data;
    }, error => {
      this.error = error.error['error']
    }).add(() => this.loading = false);
  }

  getFileIcon(f : FileObject): string {
    if (f.objType === FileObjectType.FOLDER) return 'folder';
    else if (f.type === FileExt.TYPE_MUSIC) return 'music_note';
    else if (f.type === FileExt.TYPE_MOVIE) return 'movie';
    return ''
  }

  addOrLoadFolder(f: FileObject) {
    if (f.objType === FileObjectType.FOLDER) this.loadFolder(f.id);
    else {
      this.addFileSrv.push(f);
    }
  }

  loadParentFolder() {
    if (this.currFolder.parent) this.loadFolder(this.currFolder.parent.id);
    else this.currFolder = null;
  }

  close() {
    this.mediaPlayer.fileBrowser.close();
  }

}