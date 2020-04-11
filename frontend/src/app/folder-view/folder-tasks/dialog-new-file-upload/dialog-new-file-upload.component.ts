import { Component, OnInit, Inject, Input, Output, EventEmitter } from '@angular/core';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { HttpEventType, HttpErrorResponse } from '@angular/common/http';
import { Subscription, of } from 'rxjs';
import { catchError, last, map, tap } from 'rxjs/operators';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';

@Component({
      selector: 'app-dialog-new-file-upload',
      templateUrl: './dialog-new-file-upload.component.html',
      styleUrls: ['./dialog-new-file-upload.component.css'],
      animations: [
            trigger('fadeInOut', [
                  state('in', style({ opacity: 100 })),
                  transition('* => void', [
                        animate(300, style({ opacity: 0 }))
                  ])
            ])
      ]
})
export class DialogNewFileUploadComponent implements OnInit {
      @Output() complete = new EventEmitter<string>();
      files: Array<FileUploadModel> = [];

      constructor(public dialogRef: MatDialogRef<DialogNewFileUploadComponent>,
            @Inject(MAT_DIALOG_DATA) public data: any,
            private fileService: FileService) { }

      ngOnInit() {
            this.complete.subscribe((data: object) => {
                  window.location.reload();
            });
      }

      onClick() {
            const fileUpload = document.getElementById('fileUpload') as HTMLInputElement;
            fileUpload.onchange = () => {
                  for (let i = 0; i < fileUpload.files.length; i++) this.files.push({ data: fileUpload.files[i], state: 'in', inProgress: false, progress: 0, canRetry: false, canCancel: true });
                  this.uploadFiles();
            };
            fileUpload.click();
      }

      cancelFile(file: FileUploadModel) {
            file.sub.unsubscribe();
            this.removeFileFromArray(file);
      }

      retryFile(file: FileUploadModel) {
            this.uploadFile(file);
            file.canRetry = false;
      }

      private uploadFile(file: FileUploadModel) {
            const fd = new FormData();
            fd.append('files', file.data);

            file.inProgress = true;
            file.sub = this.fileService.uploadFile(this.data, fd).pipe(
                  map(event => {
                        switch (event.type) {
                              case HttpEventType.UploadProgress:
                                    file.progress = Math.round(event.loaded * 100 / event.total);
                                    break;
                              case HttpEventType.Response:
                                    return event;
                        }
                  }),
                  tap(message => { }),
                  last(),
                  catchError((error: HttpErrorResponse) => {
                        file.inProgress = false;
                        file.canRetry = true;
                        return of(`${file.data.name} upload failed.`);
                  })
            ).subscribe(
                  (event: any) => {
                        if (typeof (event) === 'object') {
                              this.removeFileFromArray(file);
                              this.complete.emit(event.body);
                        }
                  }
            );
      }

      private uploadFiles() {
            const fileUpload = document.getElementById('fileUpload') as HTMLInputElement;
            fileUpload.value = '';
            this.files.forEach(file => this.uploadFile(file));
      }

      private removeFileFromArray(file: FileUploadModel) {
            const index = this.files.indexOf(file);
            if (index > -1) this.files.splice(index, 1);
      }

      onNoClick(): void {
            this.dialogRef.close();
      }
}

export class FileUploadModel {
      data: File;
      state: string;
      inProgress: boolean;
      progress: number;
      canRetry: boolean;
      canCancel: boolean;
      sub?: Subscription;
}