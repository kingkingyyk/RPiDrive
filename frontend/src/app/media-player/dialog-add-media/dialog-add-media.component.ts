import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';

@Component({
  selector: 'app-dialog-add-media',
  templateUrl: './dialog-add-media.component.html',
  styleUrls: ['./dialog-add-media.component.css']
})
export class DialogAddMediaComponent implements OnInit {
  newMedia = [];

  constructor(public dialogRef: MatDialogRef<DialogAddMediaComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any) {
    }

  ngOnInit(): void {
  }

  onNoClick() {
    this.dialogRef.close();
  }
}
