import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-code-viewer',
  templateUrl: './code-viewer.component.html',
  styleUrls: ['./code-viewer.component.css']
})
export class CodeViewerComponent implements OnInit {
  file : object;
  fileUrl : string;
  fileContent: string;

  constructor(
    public dialogRef: MatDialogRef<CodeViewerComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fileService: FileService) {}

  ngOnInit() {
    this.file = this.data;
    this.fileUrl = this.fileService.getFileDownloadURL(this.file['id']);
    this.fileService.getCodeContent(this.file['id']).subscribe(data => {
      this.fileContent = data;
    });
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  downloadFile(event : Event): void {
    this.fileService.downloadFile(this.file['id']);
  }
}
