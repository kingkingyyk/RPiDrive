import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-dialog-add-new-download',
  templateUrl: './dialog-add-new-download.component.html',
  styleUrls: ['./dialog-add-new-download.component.css']
})
export class DialogAddNewDownloadComponent implements OnInit {

  constructor(
    public dialogRef: MatDialogRef<DialogAddNewDownloadComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fileService: FileService) {}

  ngOnInit() {
  }

  onNoClick(): void {
    this.dialogRef.close();
  }
}
