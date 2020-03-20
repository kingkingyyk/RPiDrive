import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FileService } from 'src/app/service/file.service'
import { MatDialog } from '@angular/material/dialog';
import { DialogCreateNewFolderComponent } from './dialog-create-new-folder/dialog-create-new-folder.component';
import { DialogNewURLDownloadComponent } from './dialog-new-url-download/dialog-new-url-download.component';
import { DialogNewFileUploadComponent } from './dialog-new-file-upload/dialog-new-file-upload.component';
import { DialogNewMagnetDownloadComponent } from './dialog-new-magnet-download/dialog-new-magnet-download.component';
import { DialogNewTorrentDownloadComponent } from './dialog-new-torrent-download/dialog-new-torrent-download.component';
import { timer } from 'rxjs';

class DownloadResult {
  values: Download[];
}
class Download {
  id: string;
  name: string;
  status: string;
  downloadSpeed: string;
  progress: string;
}
@Component({
  selector: 'app-folder-tasks',
  templateUrl: './folder-tasks.component.html',
  styleUrls: ['./folder-tasks.component.css']
})
export class FolderTasksComponent implements OnInit, OnDestroy {
  storages = [];
  folderId : string;
  timerSub: any;
  downloads: Download[];

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

    this.timerSub = timer(0,10000).subscribe(t=> this.updateDownloads());
  }

  ngOnDestroy() {
    if (this.timerSub) this.timerSub.unsubscribe();
  }

  updateDownloads() {
    this.fileService.getDownloads().subscribe((data : DownloadResult) => {
      this.downloads = data.values;
    });
  }

  pauseDownload(download: Download) {
    this.fileService.pauseDownload(download.id).subscribe((data : object) => {
      this.updateDownloads();
    });
  }

  resumeDownload(download: Download) {
    this.fileService.resumeDownload(download.id).subscribe((data : object) => {
      this.updateDownloads();
    });
  }

  cancelDownload(download: Download) {
    this.fileService.cancelDownload(download.id).subscribe((data : object) => {
      this.updateDownloads();
    });
  }

  onClickUploadFile() {
    this.dialog.open(DialogNewFileUploadComponent, {data: this.folderId});
  }

  onClickCreateNewFolder() {
    this.dialog.open(DialogCreateNewFolderComponent, {data: this.folderId});
  }
  
  onClickNewURLDownload() {
    this.dialog.open(DialogNewURLDownloadComponent, {data: this.folderId});
  }

  onClickNewMagnetDownload() {
    this.dialog.open(DialogNewMagnetDownloadComponent, {data: this.folderId});
  }

  onClickNewTorrentDownload() {
    this.dialog.open(DialogNewTorrentDownloadComponent, {data: this.folderId});
  }
}
