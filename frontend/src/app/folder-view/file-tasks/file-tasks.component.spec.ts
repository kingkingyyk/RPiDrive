import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FileTasksComponent } from './file-tasks.component';

describe('FileTasksComponent', () => {
  let component: FileTasksComponent;
  let fixture: ComponentFixture<FileTasksComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FileTasksComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FileTasksComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
