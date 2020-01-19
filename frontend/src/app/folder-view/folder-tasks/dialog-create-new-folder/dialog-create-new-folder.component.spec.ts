import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogCreateNewFolderComponent } from './dialog-create-new-folder.component';

describe('DialogCreateNewFolderComponent', () => {
  let component: DialogCreateNewFolderComponent;
  let fixture: ComponentFixture<DialogCreateNewFolderComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogCreateNewFolderComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogCreateNewFolderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
