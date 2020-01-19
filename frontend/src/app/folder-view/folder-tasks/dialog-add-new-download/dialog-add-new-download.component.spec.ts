import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogAddNewDownloadComponent } from './dialog-add-new-download.component';

describe('DialogAddNewDownloadComponent', () => {
  let component: DialogAddNewDownloadComponent;
  let fixture: ComponentFixture<DialogAddNewDownloadComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogAddNewDownloadComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogAddNewDownloadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
