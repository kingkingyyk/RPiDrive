import { Component, OnInit, ViewChild, Inject } from '@angular/core';
import { FileService } from 'src/app/service/file.service';
import { ActivatedRoute } from '@angular/router';
import { SelectionModel } from '@angular/cdk/collections';
import { MatSort } from '@angular/material/sort';
import { MatDialog } from '@angular/material/dialog';
import { MatTableDataSource } from '@angular/material/table';
import { MusicPlayerComponent } from './music-player/music-player.component';
import { CodeViewerComponent } from './code-viewer/code-viewer.component';
import { PictureViewerComponent } from './picture-viewer/picture-viewer.component';
import { VideoPlayerComponent } from './video-player/video-player.component';
import { FileSelectionService } from 'src/app/service/file-selection.service';

interface Folder {
  id: string;
  name: string;
}
interface File {
  id: string;
  name: string;
  relative_path: string;
  natural_last_modified: string;
  natural_size: number;
  type: string;
  ext_type: string;
}
@Component({
  selector: 'app-file-list',
  templateUrl: './file-list.component.html',
  styleUrls: ['./file-list.component.css']
})
export class FileListComponent implements OnInit {
  displayedColumns = ['select', 'name', 'lastModified', 'size'] 
  files  = new MatTableDataSource<File>([]);
  folderId : string;
  folderName : string;
  rootFolder: Folder;
  parentFolder: Folder;
  parentFolders = [];
  selectedParentFolder: string;
  loaded = false;

  selection = new SelectionModel<File>(true, []);

  @ViewChild(MatSort, {static: true}) sort: MatSort;

  constructor(private activatedRoute: ActivatedRoute, 
              private fileService: FileService, 
              public dialog: MatDialog,
              private fileSelectionService : FileSelectionService) {}

  ngOnInit() {
    this.activatedRoute.params.subscribe( params => {
      this.folderId = params['folderId'];
      this.loadFileList();
    });
  }

  loadFileList() {
    this.loaded = false;
    this.fileService.getFileList(this.folderId).subscribe((data:  object) => {
      this.folderId = data['id'];
      this.folderName = data['name'];
      this.rootFolder = data['root-folder'];
      this.parentFolder = data['parent-folder'];
      this.parentFolders = data['parent-folders'];
      this.files = new MatTableDataSource<File>(data['files']);
      this.loaded = true;
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
    else this.fileService.downloadFile(fileObj['id']);
  }
  
  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.files.data.length;
    return numSelected === numRows;
  }

  masterToggle() {
    this.isAllSelected() ?
        this.selection.clear() :
        this.files.data.forEach(row => this.selection.select(row));
    this.onSelectionChange(null, null);
  } 

  checkboxLabel(row?: File): string {
    if (!row) {
      return `${this.isAllSelected() ? 'select' : 'deselect'} all`;
    }
    return `${this.selection.isSelected(row) ? 'deselect' : 'select'} row ${row['position'] + 1}`;
  }

  onSelectionChange(selection: SelectionModel<File>, row: File) {
    if (selection != null) selection.toggle(row);

    let selectList: Object [] = [];
    for (let f of this.selection.selected) selectList.push(f);
    this.fileSelectionService.pushUpdate(selectList);
  }
}