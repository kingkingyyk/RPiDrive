import { Component, OnInit, ViewChild, Inject } from '@angular/core';
import { FileService } from '../service/file.service';
import { ActivatedRoute } from '@angular/router';
import { SelectionModel } from '@angular/cdk/collections';
import { MatSort } from '@angular/material/sort';
import { MatDialog } from '@angular/material/dialog';
import { MusicPlayerComponent } from './music-player/music-player.component';
import { CodeViewerComponent } from './code-viewer/code-viewer.component';
import { PictureViewerComponent } from './picture-viewer/picture-viewer.component';
import { VideoPlayerComponent } from './video-player/video-player.component';

@Component({
  selector: 'app-file-list',
  templateUrl: './file-list.component.html',
  styleUrls: ['./file-list.component.css']
})
export class FileListComponent implements OnInit {
  displayedColumns  :  string[] = ['name', 'last_modified', 'size'] 
  files  = [];
  folderId : string;
  folderName : string;
  rootFolder: object;
  parentFolder: object;
  parentFolders = [];
  selectedParentFolder: string;
  selection = new SelectionModel<Object>(true, []);

  @ViewChild(MatSort, {static: true}) sort: MatSort;

  constructor(private activatedRoute: ActivatedRoute, 
              private fileService: FileService, 
              public dialog: MatDialog) {}

  ngOnInit() {
    this.activatedRoute.params.subscribe( params => {
      this.folderId = params['folderId'];
      this.loadFileList();
    });
  }

  loadFileList() {
    this.fileService.getFileList(this.folderId).subscribe((data:  object) => {
      this.folderId = data['id'];
      this.folderName = data['name'];
      this.rootFolder = data['root-folder'];
      this.parentFolder = data['parent-folder'];
      this.parentFolders = data['parent-folders'];
      this.files = data['files'];
    });
  }

  goParentFolder(folderId: string) {
    window.open("/drive/folder/"+folderId, "_self");
  }

  onClickRow(fileObj: object) {
    if (fileObj['ext_type'] == 'FOLDER') this.onClickFolder(fileObj);
    else this.onClickFile(fileObj);
  }

  onClickFolder(folderObj: object) {
    window.open("/drive/folder/"+folderObj['id'], "_self");
  }

  onClickFile(fileObj : object) {
    let targetFileObjExtType = fileObj['ext_type'];
    if (targetFileObjExtType == 'MUSIC') this.dialog.open(MusicPlayerComponent, {data: fileObj});
    else if (targetFileObjExtType == 'VIDEO') this.dialog.open(VideoPlayerComponent, {data: fileObj});
    else if (targetFileObjExtType == 'PICTURE') this.dialog.open(PictureViewerComponent, {data: fileObj});
    else if (targetFileObjExtType == 'CODE') this.dialog.open(CodeViewerComponent, {data: fileObj});
    else {
      this.fileService.downloadFile(fileObj['id']);
    }
  }

  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.files.length;
    return numSelected === numRows;
  }

  /** Selects all rows if they are not all selected; otherwise clear selection. */
  masterToggle() {
    this.isAllSelected() ?
        this.selection.clear() :
        this.files.forEach(row => this.selection.select(row));
  }

}