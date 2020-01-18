import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-music-player',
  templateUrl: './music-player.component.html',
  styleUrls: ['./music-player.component.css']
})
export class MusicPlayerComponent implements OnInit {
  file : object;
  fileUrl : string;

  constructor(
    public dialogRef: MatDialogRef<MusicPlayerComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fileService: FileService) {}

  ngOnInit() {
    this.file = this.data;
    this.fileUrl = this.fileService.getFileDownloadURL(this.file['id']);
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  downloadFile(event : Event): void {
    this.fileService.downloadFile(this.file['id']);
  }
}
