import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FileService } from 'src/app/service/file.service'
import { MatDialog } from '@angular/material/dialog';
import { DialogCreateNewFolderComponent } from './dialog-create-new-folder/dialog-create-new-folder.component';
import { DialogAddNewDownloadComponent } from './dialog-add-new-download/dialog-add-new-download.component';
import { DialogNewFileUploadComponent } from './dialog-new-file-upload/dialog-new-file-upload.component';

@Component({
  selector: 'app-folder-tasks',
  templateUrl: './folder-tasks.component.html',
  styleUrls: ['./folder-tasks.component.css']
})
export class FolderTasksComponent implements OnInit {
  storages = [];
  folderId : string;

  constructor(private activatedRoute: ActivatedRoute, 
    private fileService: FileService, 
    public dialog: MatDialog) {}

  ngOnInit() {
    this.fileService.getStorageList().subscribe((data:  Array<object>) => {
      this.storages = data;
    });
    this.activatedRoute.params.subscribe( params => {
      this.folderId = params['folderId'];
    });
  }

  onClickUploadFile() {
    this.dialog.open(DialogNewFileUploadComponent, {data: this.folderId});
  }

  onClickCreateNewFolder() {
    this.dialog.open(DialogCreateNewFolderComponent, {data: this.folderId});
  }
  
  onClickAddNewDownload() {
    this.dialog.open(DialogAddNewDownloadComponent, {data: this.folderId});
  }
}
