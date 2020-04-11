import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

interface File {
  id: string;
  name: string;
}
@Component({
  selector: 'app-rename-dialog',
  templateUrl: './rename-dialog.component.html',
  styleUrls: ['./rename-dialog.component.css']
})
export class RenameDialogComponent implements OnInit {
  file : File;
  newName = "";
  loading = false;

  constructor(public dialogRef: MatDialogRef<RenameDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: File,
              private fileService: FileService) {}

  ngOnInit() {
    this.file = this.data;
    this.newName = this.file.name;
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  renameFile() {
    this.loading = true;
    this.fileService.renameFile(this.file.id, this.newName).subscribe((data : object) => {
      this.dialogRef.close();
      window.location.reload();
    }
    ,() => {
      this.loading = false;
    });
  }
}