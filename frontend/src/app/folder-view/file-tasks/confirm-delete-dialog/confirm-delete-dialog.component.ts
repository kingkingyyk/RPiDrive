import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-confirm-delete-dialog',
  templateUrl: './confirm-delete-dialog.component.html',
  styleUrls: ['./confirm-delete-dialog.component.css']
})
export class ConfirmDeleteDialogComponent implements OnInit {
  filesToDelete : object[];
  loading = false;

  filesToDeleteDisplay : string[] = [];

  constructor(public dialogRef: MatDialogRef<ConfirmDeleteDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: object[],
    private fileService: FileService) {}

  ngOnInit() {
    this.filesToDelete = this.data;

    for (let i=0;i<=Math.min(3, this.filesToDelete.length);i++) this.filesToDeleteDisplay.push(this.filesToDelete[i]['relative_path']);
    if (this.filesToDelete.length>3) this.filesToDeleteDisplay.push('... and '+(this.filesToDelete.length-3)+' more files/folders');
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  deleteFiles(event : Event): void {
    let selectedFileIds = []
    for (let f of this.filesToDelete) selectedFileIds.push(f['id']);

    this.loading = true;
    this.fileService.deleteFiles(selectedFileIds).subscribe((data : object) => {
      this.loading = false;
      this.onNoClick();
      window.location.reload();
    });
  }
}
