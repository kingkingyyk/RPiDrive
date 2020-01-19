import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-dialog-new-file-upload',
  templateUrl: './dialog-new-file-upload.component.html',
  styleUrls: ['./dialog-new-file-upload.component.css']
})
export class DialogNewFileUploadComponent implements OnInit {

  constructor(
    public dialogRef: MatDialogRef<DialogNewFileUploadComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fileService: FileService) {}

  ngOnInit() {
  }

  onClick(): void {

  }
  
  onNoClick(): void {
    this.dialogRef.close();
  }
}
