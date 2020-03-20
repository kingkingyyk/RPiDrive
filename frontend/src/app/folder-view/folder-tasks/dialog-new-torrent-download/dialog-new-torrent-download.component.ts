import { Component, OnInit, Inject } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-dialog-new-torrent-download',
  templateUrl: './dialog-new-torrent-download.component.html',
  styleUrls: ['./dialog-new-torrent-download.component.css']
})
export class DialogNewTorrentDownloadComponent implements OnInit {

  constructor(
    public dialogRef: MatDialogRef<DialogNewTorrentDownloadComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fileService: FileService,
    private fb: FormBuilder) {
    }

  ngOnInit(): void {
  }

  add(): void {
  }
  onNoClick(): void {
    this.dialogRef.close();
  }

}
