import { Component, OnInit } from '@angular/core';
import { FileListComponent } from '../file-list/file-list.component';
import { FolderTasksComponent } from '../folder-tasks/folder-tasks.component';

@Component({
  selector: 'app-folder-view',
  templateUrl: './folder-view.component.html',
  styleUrls: ['./folder-view.component.css']
})
export class FolderViewComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

}
