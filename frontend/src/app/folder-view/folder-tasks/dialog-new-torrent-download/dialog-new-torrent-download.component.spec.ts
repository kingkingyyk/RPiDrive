import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogNewTorrentDownloadComponent } from './dialog-new-torrent-download.component';

describe('DialogNewTorrentDownloadComponent', () => {
  let component: DialogNewTorrentDownloadComponent;
  let fixture: ComponentFixture<DialogNewTorrentDownloadComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogNewTorrentDownloadComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogNewTorrentDownloadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
