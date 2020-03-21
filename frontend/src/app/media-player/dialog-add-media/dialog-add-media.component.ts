import { Component, OnInit, Inject, ViewChild, ElementRef } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { MediaPlayerService } from 'src/app/service/media-player.service';
import { FileService } from 'src/app/service/file.service';

class MediaSearchResult {
  values: MediaFile[];
}
class MediaFile {
  id: string;
  name: string;
  title: string;
  artist: string;
  album: string;
}
@Component({
  selector: 'app-dialog-add-media',
  templateUrl: './dialog-add-media.component.html',
  styleUrls: ['./dialog-add-media.component.css']
})
export class DialogAddMediaComponent implements OnInit {
  mediaToAdd = [];
  searchKeyword : string;
  searchResult : MediaFile[];
  searchLoading : boolean;

  constructor(public dialogRef: MatDialogRef<DialogAddMediaComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private service : MediaPlayerService,
    private fservice : FileService) {
    }

  ngOnInit(): void {
  }

  searchMedia() : void {
    this.searchLoading = true;
    this.service.searchMedia(this.searchKeyword).subscribe((data : MediaSearchResult) => {
      this.searchResult = data.values;
    }).add(() => this.searchLoading = false);
  }

  addMedia(media : MediaFile) {
    this.mediaToAdd.push(media);
    this.searchResult.splice(this.searchResult.indexOf(media), 1);
  }

  nowPlayingTitle : string;
  @ViewChild('audioPlayer') audioPlayerRef: ElementRef;
  playMedia(media : MediaFile) {
    this.nowPlayingTitle = media.title;
    this.audioPlayerRef.nativeElement.src = this.fservice.getFileDownloadURL(media.id);
  }

  onNoClick() {
    this.dialogRef.close();
  }
}
