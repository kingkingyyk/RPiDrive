import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FolderTasksComponent } from './folder-tasks.component';

describe('FolderTasksComponent', () => {
  let component: FolderTasksComponent;
  let fixture: ComponentFixture<FolderTasksComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FolderTasksComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FolderTasksComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
