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

  constructor(public dialogRef: MatDialogRef<ConfirmDeleteDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: object[],
    private fileService: FileService) {}

  ngOnInit() {
    this.filesToDelete = this.data;
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
      window.location.reload();
    });
  }
}
