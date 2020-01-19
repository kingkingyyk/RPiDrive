import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-picture-viewer',
  templateUrl: './picture-viewer.component.html',
  styleUrls: ['./picture-viewer.component.css']
})
export class PictureViewerComponent implements OnInit {
  file : object;
  fileUrl : string;
  bodyInfo : string;
  lensInfo : string;
  exposureInfo : string;

  constructor(
    public dialogRef: MatDialogRef<PictureViewerComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fileService: FileService) {}

  ngOnInit() {
    this.file = this.data;
    this.fileUrl = this.fileService.getFileDownloadURL(this.file['id']);

    this.bodyInfo = '';
    if (this.file['body_make']) this.bodyInfo += this.file['body_make']+' ';
    if (this.file['body_model']) this.bodyInfo += this.file['body_model'];

    this.lensInfo = '';
    if (this.file['lens_make']) this.lensInfo += this.file['lens_make']+' ';
    if (this.file['lens_model']) this.lensInfo += this.file['lens_model']+' ';
    if (this.file['focal_length']) {
      if (this.lensInfo.length > 0) this.lensInfo += '@';
      this.lensInfo += this.file['focal_length'] + ' mm';
    }
    this.exposureInfo = ''
    if (this.file['iso']) this.exposureInfo += 'ISO-' + this.file['iso']+' ';
    if (this.file['aperture']) this.exposureInfo += 'f/' + this.file['aperture']+' ';
    if (this.file['shutter_speed']) this.exposureInfo += this.file['shutter_speed'] + 's';
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  downloadFile(event : Event): void {
    this.fileService.downloadFile(this.file['id']);
  }
}
