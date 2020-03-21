import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';

@Component({
  selector: 'app-confirm-delete-playlist',
  templateUrl: './confirm-delete-playlist.component.html',
  styleUrls: ['./confirm-delete-playlist.component.css']
})
export class ConfirmDeletePlaylistComponent implements OnInit {

  constructor(public dialogRef: MatDialogRef<ConfirmDeletePlaylistComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any) {
    }

  ngOnInit(): void {
  }

  onNoClick() {
    this.dialogRef.close();
  }
}
