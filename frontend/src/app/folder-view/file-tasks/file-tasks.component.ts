import { Component, OnInit } from '@angular/core';
import { FileService } from 'src/app/service/file.service';
import { FileSelectionService } from 'src/app/service/file-selection.service';
import { ClipboardService } from 'ngx-clipboard'
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDeleteDialogComponent } from './confirm-delete-dialog/confirm-delete-dialog.component';
import { RenameDialogComponent } from './rename-dialog/rename-dialog.component';
import { MoveFileDialogComponent } from './move-file-dialog/move-file-dialog.component';

@Component({
  selector: 'app-file-tasks',
  templateUrl: './file-tasks.component.html',
  styleUrls: ['./file-tasks.component.css']
})
export class FileTasksComponent implements OnInit {
  show = false;
  showRename = false;
  showMove = false;
  showDelete = false;
  showPermalink = false;
  selectedFiles = [];

  constructor(private fileSelectionService : FileSelectionService,
              private fileService : FileService,
              public dialog: MatDialog,
              private clipboardService: ClipboardService) { }

  ngOnInit() {
    this.fileSelectionService.currentMessage.subscribe((list : object[]) => {
      this.selectedFiles = list;
      this.show = this.selectedFiles.length > 0;
      this.showRename = this.selectedFiles.length == 1;
      this.showMove = this.selectedFiles.length > 0;
      this.showDelete = this.selectedFiles.length > 0;
      this.showPermalink = this.selectedFiles.length == 1;
    });
  }

  renameSelection() {
    this.dialog.open(RenameDialogComponent, {data: this.selectedFiles[0]});
  }

  moveSelection() {
    this.dialog.open(MoveFileDialogComponent, {data: this.selectedFiles});
  }

  deleteSelection() {
    this.dialog.open(ConfirmDeleteDialogComponent, {data: this.selectedFiles});
  }

  copySelectionPermalink() {
    this.clipboardService.copyFromContent(this.fileService.getFileDownloadURL(this.selectedFiles[0].id));
  }

}