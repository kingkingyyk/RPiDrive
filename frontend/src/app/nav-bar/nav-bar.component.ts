import { Component, OnInit, Input } from '@angular/core';
import { Title }     from '@angular/platform-browser';

@Component({
  selector: 'app-nav-bar',
  templateUrl: './nav-bar.component.html',
  styleUrls: ['./nav-bar.component.css']
})
export class NavBarComponent implements OnInit {
  @Input() searchbox: boolean;
  @Input() title: string;

  public constructor(private titleService: Title) {}

  ngOnInit() {
    this.setTitle(this.title);
  }

  public setTitle( newTitle: string) {
    this.titleService.setTitle( newTitle );
  }

  openRootFolder() {
    window.open('/drive/folder', '_self')
  }
}
