import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FileService } from 'src/app/service/file.service';
import { FormGroup, FormBuilder } from '@angular/forms'
import { ValidatorFn, Validators } from '@angular/forms';
import { AbstractControl } from '@angular/forms';

@Component({
  selector: 'app-dialog-create-new-folder',
  templateUrl: './dialog-create-new-folder.component.html',
  styleUrls: ['./dialog-create-new-folder.component.css']
})
export class DialogCreateNewFolderComponent implements OnInit {
  form : FormGroup;
  folderId : string;
  folderName : string;
  caseSensitive : boolean;
  loaded : boolean;
  usedFileNames= [];
  isSubmitting : boolean;

  constructor(
    public dialogRef: MatDialogRef<DialogCreateNewFolderComponent>,
    @Inject(MAT_DIALOG_DATA) public fid: any,
    private fileService: FileService,
    private formBuilder: FormBuilder) {}

  ngOnInit() {
    this.folderId = this.fid;
    this.fileService.getFileNameList(this.folderId).subscribe((data : object) => {
        this.loaded = true;
        this.folderName = data['folder-name'];
        this.caseSensitive = data['case-sensitive'];
        this.usedFileNames = data['filenames'];
        if (!this.caseSensitive) this.usedFileNames = this.usedFileNames.map(item => item.toLowerCase());

        let idx = 0;
        let testNewFolderName = "New folder";
        while (true) {
          if (idx > 0) testNewFolderName = "New folder ("+idx+")";
          if (!this.folderNameExists(testNewFolderName)) break;
          idx += 1;
        }

        this.form = this.formBuilder.group({
          newFolderName: [testNewFolderName, [Validators.required, folderNameValidator(this)]]
        });
    });
  }

  folderNameExists(name : string){
    if (this.caseSensitive) return this.usedFileNames.includes(name);
    else return this.usedFileNames.includes(name.toLowerCase());
  }

  createNewFolder() {
    this.loaded = false;
    let stream = this.fileService.createNewFolder(this.folderId, this.form.controls["newFolderName"].value).pipe();
    stream.subscribe((data : object) => {
      this.dialogRef.close();
      window.location.reload();
    });
  }

  onNoClick(): void {
    this.dialogRef.close();
  }
}

export function folderNameValidator(diag: DialogCreateNewFolderComponent): ValidatorFn {
  return (control: AbstractControl): { [key: string]: boolean } | null => {
    if (control.value.length == 0) return {zeroLength: true};
    else if (diag.folderNameExists(control.value)) return {duplicatedName: true};
    else return null;
  };
}