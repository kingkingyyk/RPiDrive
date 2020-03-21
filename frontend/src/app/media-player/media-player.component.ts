import { Component, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MediaPlayerService } from 'src/app/service/media-player.service';
import { DialogNewPlaylistComponent } from './dialog-new-playlist/dialog-new-playlist.component';
import { FileService } from '../service/file.service';
import {CdkDragDrop, moveItemInArray} from '@angular/cdk/drag-drop';
import { timer } from 'rxjs';
import { runInThisContext } from 'vm';
import { DialogAddMediaComponent } from './dialog-add-media/dialog-add-media.component';
import { ConfirmDeletePlaylistComponent } from './confirm-delete-playlist/confirm-delete-playlist.component';
import { MatExpansionPanel } from '@angular/material';

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
        });
      }
    });
  }

  loadPlaylist(playlist : Playlist) {
    this.expPanel.expanded = false;
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
        });
      }
    })
  }

  persistPlaylist() {
    if (JSON.stringify(this.currPlaylistClean) != JSON.stringify(this.currPlaylist)) {
      this.service.updatePlaylist(this.currPlaylist).subscribe((data : Playlist) => {
        this.currPlaylistClean = data;
      })
    }
  }

  addMediaToList() {
    const diag = this.dialog.open(DialogAddMediaComponent, {data: this.currPlaylist});
    diag.afterClosed().subscribe(result => {
      if (result) {
        this.currPlaylist.files.push.apply(result);
      }
    })
  }

  reorderMedia(playlist : Playlist, event: CdkDragDrop<string[]>) {
    moveItemInArray(playlist.files, event.previousIndex, event.currentIndex);
  }

  removeMediaFromPlaylist(playlist: Playlist, file : MediaFile) {
    let index = playlist.files.indexOf(file);
    playlist.files.splice(index);
    if (playlist.files.length > 0) {
      index = index % playlist.files.length;
      if (playlist == this.currPlaylist) this.playMedia(playlist.files[index]);
    } else this.audioPlayerRef.nativeElement.src = '';
  }

  @ViewChild('audioPlayer') audioPlayerRef: ElementRef;
  playMedia(file : MediaFile) {
    this.currPlayingMedia = file;
    this.currPlayingIndex = this.currPlaylist.files.indexOf(this.currPlayingMedia);
    this.audioPlayerRef.nativeElement.src = this.fservice.getFileDownloadURL(this.currPlayingMedia.id);
  }

  onAudioEnded() {
    this.currPlayingIndex = (this.currPlaylist.files.indexOf(this.currPlayingMedia) + 1) % this.currPlaylist.files.length;
    this.currPlayingMedia = this.currPlaylist.files[this.currPlayingIndex];
    this.audioPlayerRef.nativeElement.src = this.fservice.getFileDownloadURL(this.currPlayingMedia.id);
  }
}
