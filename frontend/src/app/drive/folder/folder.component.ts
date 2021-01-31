import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';

@Component({
  selector: 'app-folder',
  templateUrl: './folder.component.html',
  styleUrls: ['./folder.component.scss']
})
export class FolderComponent implements OnInit {

  constructor(private service: CommonService,
              private router: Router,
              private titleService: Title) {
                this.titleService.setTitle('File Explorer - RPi Drive');
              }

  ngOnInit(): void {
  }

}
