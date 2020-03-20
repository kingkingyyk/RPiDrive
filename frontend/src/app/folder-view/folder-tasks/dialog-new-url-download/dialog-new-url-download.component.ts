import { Component, OnInit, Inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-dialog-new-url-download',
  templateUrl: './dialog-new-url-download.component.html',
  styleUrls: ['./dialog-new-url-download.component.css']
})
export class DialogNewURLDownloadComponent implements OnInit {
  fg: FormGroup;

  constructor(
    public dialogRef: MatDialogRef<DialogNewURLDownloadComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fileService: FileService,
    private fb: FormBuilder) {
      this.fg = this.fb.group({
        url: [null, Validators.required],
        filename: [null],
        authentication: [false],
        username: [null],
        password: [null]
      })
    }

  ngOnInit() {
  }

  add(): void {
    this.fileService.addURLDownload(this.fg.value).subscribe((data : object) => {
      this.dialogRef.close();
    }, error => {
      alert('error!');
    });
  }
  onNoClick(): void {
    this.dialogRef.close();
  }
}
