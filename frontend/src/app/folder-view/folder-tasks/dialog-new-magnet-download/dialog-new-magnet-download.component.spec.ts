import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogNewMagnetDownloadComponent } from './dialog-new-magnet-download.component';

describe('DialogNewMagnetDownloadComponent', () => {
  let component: DialogNewMagnetDownloadComponent;
  let fixture: ComponentFixture<DialogNewMagnetDownloadComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogNewMagnetDownloadComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogNewMagnetDownloadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
