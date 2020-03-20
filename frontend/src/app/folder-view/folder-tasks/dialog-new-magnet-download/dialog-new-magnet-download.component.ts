import { Component, OnInit, Inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-dialog-new-magnet-download',
  templateUrl: './dialog-new-magnet-download.component.html',
  styleUrls: ['./dialog-new-magnet-download.component.css']
})
export class DialogNewMagnetDownloadComponent implements OnInit {
  fg: FormGroup;

  constructor(
    public dialogRef: MatDialogRef<DialogNewMagnetDownloadComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fileService: FileService,
    private fb: FormBuilder) {
      this.fg = this.fb.group({
        url: [null, Validators.required],
      })
    }

  ngOnInit(): void {
  }

  add(): void {
    this.fileService.addMagnetDownload(this.fg.value).subscribe((data : object) => {
      this.dialogRef.close();
    }, error => {
      alert('error!');
    });
  }
  onNoClick(): void {
    this.dialogRef.close();
  }
  
}
