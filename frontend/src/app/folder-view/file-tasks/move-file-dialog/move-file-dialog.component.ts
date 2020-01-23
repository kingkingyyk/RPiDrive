import { Component, OnInit, Inject, Injectable } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-move-file-dialog',
  templateUrl: './move-file-dialog.component.html',
  styleUrls: ['./move-file-dialog.component.css'],
})
export class MoveFileDialogComponent implements OnInit {
  filesToMove : object[];
  filesIdToMove : string [] = [];

  loading = true;
  currFolder : object;
  currChildFolders : object [];

  constructor(public dialogRef: MatDialogRef<MoveFileDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: object [],
              public service: FileService) {}

  ngOnInit() {
    this.filesToMove = this.data;
    for (let files of this.filesToMove) this.filesIdToMove.push(files['id']);
    this.loadFolder(null);
  }

  loadFolder(folder: object) {
    let folderID = (folder == null) ? null : folder['id'];
    this.loading = true;
    this.service.getFolderList(folderID).subscribe((data : object) => {
      this.currFolder = {id: data['id'], name: data['name'], parentFolder: {id: data['parent-folder']}};
      this.currChildFolders = data['folders'];
      this.loading = false;
    });
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  moveFiles() {
    this.loading = true;
    this.service.moveFiles(this.filesIdToMove, this.currFolder['id']).subscribe((data : object) => {
      this.onNoClick();
      window.open('/drive/folder/' + this.currFolder['id'], '_self');
    });
  };
}