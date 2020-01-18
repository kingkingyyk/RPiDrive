import { Component, OnInit } from '@angular/core';
import { FileService } from '../service/file.service'

@Component({
  selector: 'app-folder-tasks',
  templateUrl: './folder-tasks.component.html',
  styleUrls: ['./folder-tasks.component.css']
})
export class FolderTasksComponent implements OnInit {
  storages = []

  constructor(private fileService: FileService) {}

  ngOnInit() {
    this.fileService.getStorageList().subscribe((data:  Array<object>) => {
      this.storages = data;
    });
  }

}
