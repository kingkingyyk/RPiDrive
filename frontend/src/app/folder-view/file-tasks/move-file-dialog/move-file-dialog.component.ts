import { Component, OnInit, Inject, Injectable } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

interface File {
  id: string;
  name: string;
}
class Folder {
  id: string;
  name: string;
  parentFolder: Folder;
  constructor (i: string, n: string, p: string) {
    this.id=i;
    this.name=n;
    if (p!=null) this.parentFolder=new Folder(p,'',null);
  }
}
@Component({
  selector: 'app-move-file-dialog',
  templateUrl: './move-file-dialog.component.html',
  styleUrls: ['./move-file-dialog.component.css'],
})
export class MoveFileDialogComponent implements OnInit {
  filesToMove : File[];
  filesIdToMove : string [] = [];

  loading = true;
  currFolder : Folder;
  currChildFolders : Folder [];

  constructor(public dialogRef: MatDialogRef<MoveFileDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: File [],
              public service: FileService) {}

  ngOnInit() {
    this.filesToMove = this.data;
    for (let files of this.filesToMove) this.filesIdToMove.push(files.id);
    this.loadFolder(null);
  }

  loadFolder(folder: Folder) {
    let folderID = (folder == null) ? null : folder.id;
    this.loading = true;
    this.service.getFolderList(folderID).subscribe((data : object) => {
      this.currFolder = new Folder(data['id'], data['name'], data['parent-folder']);
      this.currChildFolders = data['folders'];
      this.loading = false;
    });
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  moveFiles() {
    this.loading = true;
    this.service.moveFiles(this.filesIdToMove, this.currFolder.id).subscribe((data : object) => {
      this.onNoClick();
      window.open('/drive/folder/' + this.currFolder.id, '_self');
    });
  };
}