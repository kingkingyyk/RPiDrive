import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogNewURLDownloadComponent } from './dialog-new-url-download.component';

describe('DialogNewURLDownloadComponent', () => {
  let component: DialogNewURLDownloadComponent;
  let fixture: ComponentFixture<DialogNewURLDownloadComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogNewURLDownloadComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogNewURLDownloadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
