import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FormGroup, FormBuilder } from '@angular/forms'
import { Validators } from '@angular/forms';

@Component({
  selector: 'app-dialog-new-playlist',
  templateUrl: './dialog-new-playlist.component.html',
  styleUrls: ['./dialog-new-playlist.component.css']
})
export class DialogNewPlaylistComponent implements OnInit {
  formGroup : FormGroup;
  constructor(public dialogRef: MatDialogRef<DialogNewPlaylistComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private formBuilder: FormBuilder) {
      this.formGroup = this.formBuilder.group({
        name: [data['name'], Validators.required]
      })
    }

  ngOnInit(): void {
  }

  onNoClick() {
    this.dialogRef.close();
  }
}
