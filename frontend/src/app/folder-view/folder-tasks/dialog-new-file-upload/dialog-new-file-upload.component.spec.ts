import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogNewFileUploadComponent } from './dialog-new-file-upload.component';

describe('DialogNewFileUploadComponent', () => {
  let component: DialogNewFileUploadComponent;
  let fixture: ComponentFixture<DialogNewFileUploadComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogNewFileUploadComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogNewFileUploadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
