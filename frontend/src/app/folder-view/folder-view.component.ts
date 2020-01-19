import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { FileService } from 'src/app/service/file.service';

@Component({
  selector: 'app-folder-view',
  templateUrl: './folder-view.component.html',
  styleUrls: ['./folder-view.component.css']
})
export class FolderViewComponent implements OnInit {
  folderId : string;

  constructor(private router: Router,
              private activatedRoute: ActivatedRoute, 
              private fileService: FileService) {}

  ngOnInit() {
    this.activatedRoute.params.subscribe( params => {
      let currId = params['folderId'];
      this.fileService.getFolderRedirect(currId).subscribe((data:  object) => {
        let redirectedId = data['id'];
        if (currId != redirectedId) {
          window.open("/drive/folder/"+redirectedId, "_self");
        }
      });
    });
  }

}
