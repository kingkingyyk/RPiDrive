import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MediaPlayerService } from 'src/app/service/media-player.service';
import { DialogNewPlaylistComponent } from './dialog-new-playlist/dialog-new-playlist.component';
import { FileService } from '../service/file.service';
import {CdkDragDrop, moveItemInArray} from '@angular/cdk/drag-drop';
import { timer } from 'rxjs';
import { DialogAddMediaComponent } from './dialog-add-media/dialog-add-media.component';
import { ConfirmDeletePlaylistComponent } from './confirm-delete-playlist/confirm-delete-playlist.component';
import { MatExpansionPanel } from '@angular/material';
import { Title } from '@angular/platform-browser';

interface GetPlaylistsResult {
  values: Playlist[];
}
interface Playlist {
  id: string;
  name: string;
  user: string;
  mediaCount: string;
  files: MediaFile[];
}
interface MediaFile {
  id: string;
  name: string;
}
@Component({
  selector: 'app-media-player',
  templateUrl: './media-player.component.html',
  styleUrls: ['./media-player.component.css']
})
export class MediaPlayerComponent implements OnInit, OnDestroy {
  updateTimer : any;
  playlists : Playlist[];
  currPlaylistClean : Playlist;
  currPlaylist : Playlist;
  currPlayingMedia : MediaFile;
  currPlayingIndex = 0;
  playlistSearchKeyword = '';

  @ViewChild('expPanel') expPanel : MatExpansionPanel;

  constructor(private service : MediaPlayerService,
              private fservice : FileService,
              private titleService: Title,
              private dialog: MatDialog) {}

  ngOnInit(): void {
    this.searchPlaylist();
    this.updateTimer = timer(0,10000).subscribe(() => this.persistPlaylist());
  }

  ngOnDestroy() : void {
    if (this.updateTimer) this.updateTimer.unsubscribe();
  }

  openNewPlaylistDialog() {
    const diag = this.dialog.open(DialogNewPlaylistComponent, {data: {name: '', new: true}});
    diag.afterClosed().subscribe(result => {
      if (result) {
        this.expPanel.expanded = false;
        this.service.createPlaylist(result['name']).subscribe((data : Playlist) => {
          this.playlists.unshift(data);
          this.loadPlaylist(data);
        }, error => {
          alert('error');
        });
      }
    });
  }

  loadPlaylist(playlist : Playlist) {
    this.expPanel.expanded = false;
    this.currPlayingMedia = null;
    this.currPlayingIndex = -1
    this.audioPlayerRef.nativeElement.src = '';
    this.service.getPlaylist(playlist.id).subscribe((data : Playlist) => {
      this.currPlaylistClean = JSON.parse(JSON.stringify(data));
      this.currPlaylist = data;
      if (this.currPlaylist.files.length > 0) this.playMedia(this.currPlaylist.files[0]);
    })
  }

  searchPlaylist() {
    this.service.searchPlaylists(this.playlistSearchKeyword).subscribe((data : GetPlaylistsResult) => {
      this.playlists = data.values;
    });
  }

  renamePlaylist(playlist: Playlist) {
    const diag = this.dialog.open(DialogNewPlaylistComponent, {data: {name: playlist.name, new: false}});
    diag.afterClosed().subscribe(result => {
      if (result) {
        playlist.name = result['name'];
      }
    });
  }

  deletePlaylist(playlist: Playlist) {
    const diag = this.dialog.open(ConfirmDeletePlaylistComponent);
    diag.afterClosed().subscribe(result => {
      if (result) {
        this.expPanel.expanded = true;
        this.service.deletePlaylist(playlist).subscribe((data : object) => {
          this.searchPlaylist();
          if (this.currPlaylist == playlist) {
            this.currPlaylist = null;
            this.currPlaylistClean = null;
          }
        }, error => {
          alert('error');
        });
      }
    })
  }

  persistPlaylist() {
    if (JSON.stringify(this.currPlaylistClean) != JSON.stringify(this.currPlaylist)) {
      this.service.updatePlaylist(this.currPlaylist).subscribe((data : Playlist) => {
        this.currPlaylist = data;
        this.currPlaylistClean = JSON.parse(JSON.stringify(this.currPlaylist));
      })
    }
  }

  addMediaToList() {
    const diag = this.dialog.open(DialogAddMediaComponent, {data: this.currPlaylist});
    diag.afterClosed().subscribe(result => {
      if (result) {
        this.currPlaylist.files.push(...result);
        if (!this.currPlayingMedia && this.currPlaylist.files.length > 0) {
          if (this.currPlaylist.files.indexOf(this.currPlayingMedia) > 0) this.audioPlayerRef.nativeElement.play();
          else this.playMedia(this.currPlaylist.files[0]);
        }
        this.persistPlaylist();
      }
    })
  }

  reorderMedia(playlist : Playlist, event: CdkDragDrop<string[]>) {
    moveItemInArray(playlist.files, event.previousIndex, event.currentIndex);
  }

  removeMediaFromPlaylist(playlist: Playlist, file : MediaFile) {
    let index = -1;
    for (let i=0;i<playlist.files.length;i++) if (playlist.files[i].id === file.id) {
      index = i;
      break;
    }
    
    if (index >= 0) {
      playlist.files.splice(index,1);
      if (playlist.files.length > 0) {
        index = index % playlist.files.length;
        if (playlist.id == this.currPlaylist.id) this.playMedia(this.currPlaylist.files[index]);
      } else this.audioPlayerRef.nativeElement.src = '';
    }
  }

  @ViewChild('audioPlayer') audioPlayerRef: ElementRef;
  playMedia(file : MediaFile) {
    if (this.currPlayingMedia === file) {
      if (this.audioPlayerRef.nativeElement.paused) {
        this.audioPlayerRef.nativeElement.play();
        this.titleService.setTitle('Now playing - '+file.name);
      }
      else {
        this.audioPlayerRef.nativeElement.pause();
        this.titleService.setTitle('Paused - '+file.name);
      }
    } else {
      this.currPlayingMedia = file;
      this.currPlayingIndex = this.currPlaylist.files.indexOf(this.currPlayingMedia);
      this.audioPlayerRef.nativeElement.src = this.fservice.getFileDownloadURL(this.currPlayingMedia.id);
      this.audioPlayerRef.nativeElement.play();
      this.titleService.setTitle('Now playing - '+file.name);
    }

  }

  onAudioEnded() {
    this.currPlayingIndex = (this.currPlaylist.files.indexOf(this.currPlayingMedia) + 1) % this.currPlaylist.files.length;
    this.currPlayingMedia = this.currPlaylist.files[this.currPlayingIndex];
    this.audioPlayerRef.nativeElement.src = this.fservice.getFileDownloadURL(this.currPlayingMedia.id);
    this.titleService.setTitle('Now playing - '+this.currPlayingMedia.name);
  }
}
